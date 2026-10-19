import os
import time
import json
import requests
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from dotenv import load_dotenv
load_dotenv() 

# Import modul fungsi migrasi otomatis
from migration import run_migrations

# Konfigurasi pembacaan environment
DB_CONFIG = os.getenv("DB_CONFIG", "dbname=ticketing_support user=postgres password=password123 host=127.0.0.1 port=5432")
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_SYSTEMONE_URL = f"{OLLAMA_BASE_URL}/v1/systemone"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[*] Aplikasi startup: Menjalankan migrasi database...")
    run_migrations()
    yield
    print("[*] Aplikasi shutdown...")

app = FastAPI(
    title="Ollama Jev Triage Router Service",
    description="Microservice untuk klasifikasi cepat teks menggunakan model Jev tev1",
    version="1.0.0",
    lifespan=lifespan
)

templates = Jinja2Templates(directory="templates")

# =====================================================================
# CORE LOGIC & BACKEND UTILITIES
# =====================================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=6),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    reraise=True
)
def call_ollama_api(payload):
    print("[*] Mengirim permintaan ke model Tev1 di Ollama...")
    response = requests.post(OLLAMA_SYSTEMONE_URL, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()

def save_log_to_db(final_state: str, raw_response: dict, execution_time_ms: int):
    try:
        conn = psycopg2.connect(DB_CONFIG)
        cur = conn.cursor()
        query_insert_log = """
        INSERT INTO jev_execution_logs (
            model_id, prompt_template_id, final_state_sent, raw_response_json, execution_time_ms
        ) VALUES (
            (SELECT id FROM ollama_models WHERE model_name = 'tev1:0.8b' LIMIT 1),
            (SELECT id FROM prompt_templates WHERE template_name = 'Customer Ticket Router' LIMIT 1),
            %s, %s, %s
        );
        """
        cur.execute(query_insert_log, (final_state, json.dumps(raw_response), execution_time_ms))
        conn.commit()
        cur.close()
        conn.close()
        print(f"[✓] Background Task: Log berhasil diamankan di DB ({execution_time_ms}ms)")
    except Exception as e:
        print(f"[-] Background Task Error: Gagal menyimpan log: {e}")

def get_recent_logs(limit=15):
    try:
        conn = psycopg2.connect(DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT l.id, m.model_name, l.final_state_sent, l.raw_response_json, l.execution_time_ms, l.created_at
            FROM jev_execution_logs l
            JOIN ollama_models m ON l.model_id = m.id
            ORDER BY l.created_at DESC
            LIMIT %s;
        """
        cur.execute(query, (limit,))
        rows = cur.fetchall()
        
        for row in rows:
            row['answers'] = row['raw_response_json'].get('answers', {})
            
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"[-] Gagal mengambil data log dari DB: {e}")
        return []

def get_latency_chart_data():
    try:
        conn = psycopg2.connect(DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT 
                TO_CHAR(DATE_TRUNC('minute', created_at), 'HH24:MI') as minute_bucket,
                ROUND(AVG(execution_time_ms)) as avg_latency
            FROM jev_execution_logs
            WHERE created_at >= NOW() - INTERVAL '3000 minute'
            GROUP BY minute_bucket
            ORDER BY minute_bucket ASC;
        """
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        labels = [row['minute_bucket'] for row in rows]
        values = [float(row['avg_latency']) for row in rows]
        return labels, values
    except Exception as e:
        print(f"[-] Gagal mengambil data grafik dari DB: {e}")
        return [], []

# =====================================================================
# DASHBOARD INTERACTIVE ENDPOINTS (FASTAPI + HTMX)
# =====================================================================

@app.get("/dashboard", response_class=HTMLResponse)
def view_dashboard(request: Request):
    logs = get_recent_logs(15)
    labels, values = get_latency_chart_data()
    return templates.TemplateResponse(
        request,  # <-- 'request' must be the 1st positional parameter!
        "dashboard.html", 
        {
            "logs": logs,
            "chart_labels": labels,
            "chart_values": values
        }
    )

@app.get("/dashboard/table", response_class=HTMLResponse)
def view_dashboard_table_partial(request: Request):
    logs = get_recent_logs(15)
    return templates.TemplateResponse(
        request,
        "table_partial.html", 
        {"logs": logs}
    )

@app.get("/dashboard/chart-data")
def view_chart_data_api():
    labels, values = get_latency_chart_data()
    return JSONResponse(content={"labels": labels, "values": values})

@app.post("/dashboard/submit", response_class=HTMLResponse)
def handle_dashboard_form_submit(
    request: Request,
    background_tasks: BackgroundTasks,
    user_message: str = Form(...),
    decision_set_id: int = Form(1)
):
    try:
        conn = psycopg2.connect(DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        query_get_schema = """
        SELECT jsonb_object_agg(jq.question_key, jsonb_build_object(
            'type', jq.decision_type, 'instructions', jq.instructions,
            'criteria', CASE 
                WHEN jq.decision_type = 'noul' THEN NULL
                WHEN jq.decision_type = 'score' THEN (SELECT jsonb_agg(jc.option_description ORDER BY jc.sort_order) FROM jev_criteria jc WHERE jc.question_id = jq.id)
                ELSE (SELECT jsonb_object_agg(jc.option_key, jc.option_description) FROM jev_criteria jc WHERE jc.question_id = jq.id)
            END
        )) AS formatted_questions FROM jev_questions jq WHERE jq.decision_set_id = %s;
        """
        cur.execute(query_get_schema, (decision_set_id,))
        schema_row = cur.fetchone()
        
        if not schema_row or not schema_row['formatted_questions']:
            raise HTTPException(status_code=404, detail="Decision set tidak ditemukan atau kosong")
            
        ollama_questions_schema = schema_row['formatted_questions']
        final_state = f"User Message: {user_message} | Platform: Web_Dashboard"
        
        cur.close()
        conn.close()
        
        start_time = time.time()
        payload = {
            "model": "tev1:0.8b",
            "state": final_state,
            "questions": ollama_questions_schema
        }
        raw_response = call_ollama_api(payload)
        end_time = time.time()
        
        execution_time_ms = int((end_time - start_time) * 1000)
        background_tasks.add_task(save_log_to_db, final_state, raw_response, execution_time_ms)
        
        time.sleep(0.2) 
        logs = get_recent_logs(15)
        return templates.TemplateResponse(
            request,                # 1. Pindahkan 'request' ke posisi pertama!
            "table_partial.html",   # 2. Nama template di posisi kedua
            {"logs": logs}          # 3. Context dictionary di posisi ketiga
        )

    except requests.exceptions.RequestException as http_err:
        raise HTTPException(status_code=503, detail=f"Ollama Service Down: {str(http_err)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses data form: {str(e)}")
