import psycopg2
import os
import time

from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = os.getenv("DB_CONFIG", "dbname=ticketing_support user=postgres password=password123 host=127.0.0.1 port=5432")


DDL_SQL = """
-- 1. Tabel Master Model Ollama
CREATE TABLE IF NOT EXISTS ollama_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL UNIQUE,
    parameter_size VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabel Template Prompt
CREATE TABLE IF NOT EXISTS prompt_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL,
    base_state_template TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabel Group Pertanyaan Jev
CREATE TABLE IF NOT EXISTS decision_sets (
    id SERIAL PRIMARY KEY,
    set_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabel Detail Pertanyaan Jev
CREATE TABLE IF NOT EXISTS jev_questions (
    id SERIAL PRIMARY KEY,
    decision_set_id INT REFERENCES decision_sets(id) ON DELETE CASCADE,
    question_key VARCHAR(50) NOT NULL,
    decision_type VARCHAR(10) NOT NULL,
    instructions TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(decision_set_id, question_key)
);

-- 5. Tabel Kriteria Pilihan
CREATE TABLE IF NOT EXISTS jev_criteria (
    id SERIAL PRIMARY KEY,
    question_id INT REFERENCES jev_questions(id) ON DELETE CASCADE,
    option_key VARCHAR(50) NOT NULL,
    option_description TEXT,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Tabel Log Audit
CREATE TABLE IF NOT EXISTS jev_execution_logs (
    id BIGSERIAL PRIMARY KEY,
    model_id INT REFERENCES ollama_models(id),
    prompt_template_id INT REFERENCES prompt_templates(id),
    final_state_sent TEXT NOT NULL,
    raw_response_json JSONB NOT NULL,
    execution_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SEED_SQL = """
-- Pengisian data awal jika tabel masih kosong
INSERT INTO ollama_models (model_name, parameter_size) VALUES ('tev1:0.8b', '0.8B') ON CONFLICT DO NOTHING;
INSERT INTO prompt_templates (template_name, base_state_template) VALUES ('Customer Ticket Router', 'User Message: {{user_message}} | Platform: Mobile_App') ON CONFLICT DO NOTHING;

INSERT INTO decision_sets (id, set_name, description) VALUES (1, 'Triage Kasus Support', 'Set evaluasi awal tiket masuk') ON CONFLICT DO NOTHING;

INSERT INTO jev_questions (id, decision_set_id, question_key, decision_type, instructions) VALUES 
(1, 1, 'deteksi_marah', 'noul', 'Apakah user menyampaikan keluhan dengan nada marah atau frustrasi?'),
(2, 1, 'kategori_layanan', 'choice', 'Kategori departemen mana yang paling cocok menangani masalah ini?')
ON CONFLICT DO NOTHING;

INSERT INTO jev_criteria (question_id, option_key, option_description) VALUES 
(2, 'billing', 'Masalah terkait kegagalan transaksi pembayaran atau langganan premium.'),
(2, 'technical', 'Masalah aplikasi error, crash, gagal memuat halaman, atau bug.'),
(2, 'general', 'Pertanyaan umum mengenai cara penggunaan fitur aplikasi.')
ON CONFLICT DO NOTHING;
"""

def run_migrations():
    print("[*] Mencoba terhubung ke database untuk migrasi...")
    for i in range(10):
        try:
            conn = psycopg2.connect(DB_CONFIG)
            cur = conn.cursor()
            
            # Jalankan pembuatan struktur tabel dan seed data awal
            cur.execute(DDL_SQL)
            cur.execute(SEED_SQL)
            
            conn.commit()
            cur.close()
            conn.close()
            print("[✓] Migrasi database dan seeding data awal sukses dilakukan!")
            return
        except psycopg2.OperationalError:
            print(f"[*] Database belum siap, mencoba ulang dalam 2 detik... ({i+1}/10)")
            time.sleep(2)
            
    print("[-] Gagal melakukan migrasi database. PostgreSQL tidak merespon.")

if __name__ == "__main__":
    run_migrations()
