
📊 Ticketing Support Demo (Jev Tev1)

An open-source, ultra-lightweight, and low-latency Automated Ticket Triage Microservice built on top of Ollama's System One / Jev-Style Decision Model ecosystem.

This repository leverages Ollama 0.35+ running a locally hosted tev1:0.8b classifier model (0.8 Billion parameters, ~812 MB footprint) to evaluate incoming customer support requests instantly without long prose generations or text hallucinations. It features a modern, async monitoring dashboard styled with Tailwind CSS v4 and powered by htmx v4 for seamless interactive operations.


![Dashboard](/storage/dashboard.png)

![Dashboard-Popup](/storage/dashboard_popup.png)


🏗️ Project Architecture & Stack

```text
ticketing-support-demo/
├── .venv/               # Isolated Python Environment
├── .env                 # Local Application Configurations (Ignored by Git)
├── .gitignore           # Git Exclusion Schema
├── requirements.txt     # Python Dependencies
├── app_fastapi.py       # Core REST API Gateway & Dashboard Controls
├── migration.py         # Automated Database Schema Installer & Seeder
└── templates/           # Server-side HTML Views
    ├── dashboard.html   # Main Monitoring Application UI (Jinja2 + Chart.js)
    └── table_partial.html # Dynamic Table Fragment used by htmx
```

- Backend Framework: FastAPI (Python 3.14 compatible, utilizing modern async background workers).
- AI Engine Layer: Ollama 0.35+ (/v1/systemone endpoint) orchestrating the tev1:0.8b decision model.
- Database Persistence: PostgreSQL 15 (Docker Container layer) storing configuration questions, criteria labels, and historical audit logs.
- Frontend Interactivity: htmx v4 (Kebab-case event layer) delivering an SPA-like single-page dashboard layout without massive JavaScript node overheads.
- Data Visualization: Chart.js (Interstellar smooth updates on real-time average processing latency).

🛠️ Prerequisites & Infrastructure

Before booting up the microservice, ensure your local Ubuntu machine satisfies the following hardware and runtime software baseline metrics:

1. Upgrade Local Ollama to 0.35+

The Jev-style typed dictionary schema requires Ollama's SystemOne engine. Upgrade and verify your background server daemon:
```bash
# Force install Ollama 0.35+
curl -fsSL https://ollama.com | OLLAMA_VERSION=0.35.0 sh

# Restart systemd background runner
sudo systemctl restart ollama

# Verify active CLI version
ollama --version
```

2. Cache the Decision Model Locally

Pull the lightweight experimental tev1:0.8b model from the registry repository:
```bash
ollama pull tev1:0.8b
```

3. Spin Up an External Isolated PostgreSQL Container

Expose port 5432 to your system host loopback layer:
```bash
docker run -d \
  --name local-postgres-triage \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password123 \
  postgres:15-alpine
```
Log inside the database instance to create the schema placeholder manually:
```bash
docker exec -it local-postgres-triage psql -U postgres -c "CREATE DATABASE ticketing_support;"
```

🚀 Installation & Local Execution


1. Clone & Set Up the Python Virtual Environment

Create a clean runtime layer using the venv architecture:
```bash
cd ticketing-support-demo
python3 -m venv .venv
source .venv/bin/activate
```

2. Install Dependencies Bundle

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. Configure Local Environment File (.env)

Create a .env file in the root directory:
```env
DB_CONFIG="dbname=ticketing_support user=postgres password=password123 host=127.0.0.1 port=5432"
OLLAMA_URL="http://localhost:11434"
```

4. Fire Up the Server Gateway

Run the async Uvicorn server wrapper. The code lifespan block will automatically detect the database state and trigger migration.py to seed initialization values:
```bash
uvicorn app_fastapi:app --host 0.0.0.0 --port 8000 --reload
```
Open your target browser engine and navigate to the local management suite:
👉 http://localhost:8000/dashboard

🧪 Simulation Prompts for Evaluation

Copy and paste these real-world sample inputs into your local dashboard text area layer to evaluate the model's accuracy, conditional logic routing, and performance markers:
- Angry Account Lockout (High Urgency, Sentiment Trigger):
"APLIKASI SANGAT JELEK! Saya baru saja mengisi token premium tapi saldo saldo dompet saya hilang misterius!! Kembalikan uang saya sekarang atau saya bawa kasus ini ke jalur hukum!"

Expected Outcome: deteksi_marah: true (~0.90+ probability), kategori_layanan: billing.
- Application System Bug (Technical Support Routing):
"Setiap kali saya membuka tab riwayat invoice transaksi di handphone Android, aplikasinya mendadak freeze lalu tertutup sendiri otomatis tanpa kode error."

Expected Outcome: deteksi_marah: false, kategori_layanan: technical.
- General Feature Inquiry (Anticipated Base Queue):
"Apakah aplikasi kasir digital ini sudah mendukung pencetakan cetak struk via bluetooth thermal printer merk Panda?"

Expected Outcome: deteksi_marah: false, kategori_layanan: general.

🔒 Production Readiness & Monitoring

- Resilient Request Retries: Network delays or background engine wake timeouts are mitigated via tenacity exponential backoffs, safely retrying connections up to 3 times before applying an atomic database rollback.
- No UI Rendering Pipeline Freezes: Writing execution log metrics to jev_execution_logs is handed off to isolated FastAPI asynchronous background task workers, returning responses back to users instantly while processing analytical logging out of band.

