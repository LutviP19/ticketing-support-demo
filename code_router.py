import os
import requests
import json
import time
import sys
import threading
from dotenv import load_dotenv

load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Global variable untuk mengontrol status animasi loading
loading_active = False

def triage_code_with_jev(code_snippet: str):
    """
    Tahap 1: Memeriksa kode menggunakan model klasifikasi Jev (tev1:0.8b)
    """
    url = f"{OLLAMA_URL}/v1/systemone"
    
    payload = {
        "model": "tev1:0.8b",
        "state": f"Code Snippet:\n{code_snippet}",
        "questions": {
            "has_syntax_error": {
                "type": "noul", # Tipe keputusan Ya/Tidak (True/False)
                "instructions": "Apakah kode pemrograman di atas memiliki kesalahan sintaks murni (broken logic/syntax error)?"
            }
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # Ekstraksi hasil keputusan tipe noul
        answers = result.get("answers", {})
        has_error = answers.get("has_syntax_error", {}).get("noul", False)
        
        return has_error
    except Exception as e:
        print(f"[-] Gagal terhubung ke model Jev: {e}")
        return False

def animate_loading(message):
    """
    Dynamic loading spinner animation running on an isolated background thread
    """
    global loading_active
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    idx = 0
    
    while loading_active:
        # FIXED: Removed the invalid \ ( and \ ) wrappers. Only use \r for the carriage return.
        sys.stdout.write(f"\r{spinner[idx]} {message}")
        sys.stdout.flush()
        idx = (idx + 1) % len(spinner)
        time.sleep(0.1)
        
    # FIXED: Replaced clean blank line string clearing mechanism smoothly
    sys.stdout.write("\r" + " " * (len(message) + 4) + "\r")
    sys.stdout.flush()

def fix_code_with_codegemma(broken_code: str):
    """
    Tahap 2: Memperbaiki kode menggunakan model CodeGemma dengan Animasi Loading (Timeout: Unlimited)
    """
    global loading_active
    url = f"{OLLAMA_URL}/api/generate"
    
    prompt = f"""
    Kamu adalah asisten pemrograman AI senior. Kode Python berikut mengalami syntax error atau cacat logika:
    
    ```python
    {broken_code}
    ```
    
    Tolong perbaiki kode di atas agar dapat dieksekusi dengan benar. Berikan kode hasil perbaikan di dalam blok markdown python beserta penjelasan singkat kerusakannya.
    Perbaikan:
    """
    
    payload = {
        "model": "codegemma:2b",
        "prompt": prompt,
        "stream": False
    }
    
    # Sediakan variabel penampung respon antar-thread
    response_container = {"text": "", "error": None}
    
    def target_api_call():
        try:
            response = requests.post(url, json=payload, timeout=None)
            response.raise_for_status()
            response_container["text"] = response.json().get("response", "")
        except Exception as e:
            response_container["error"] = e

    # 1. Aktifkan flag loading & Nyalakan Thread Animasi
    loading_active = True
    msg = "[*] Mengeskalasi masalah ke LLM Utama (codegemma) untuk penulisan perbaikan kode..."
    loading_thread = threading.Thread(target=animate_loading, args=(msg,))
    loading_thread.start()
    
    # 2. Jalankan Tembakan API di Thread Berbeda agar tidak mengunci animasi
    api_thread = threading.Thread(target=target_api_call)
    api_thread.start()
    
    # Tunggu sampai proses API selesai dikalkulasi oleh CodeGemma
    api_thread.join()
    
    # 3. Matikan Animasi Loading setelah API mengembalikan data
    loading_active = False
    loading_thread.join()
    
    # 4. Tampilkan Hasil atau Error
    if response_container["error"]:
        return f"[-] Gagal memanggil model CodeGemma: {response_container['error']}"
        
    print("[✓] Respon berhasil diterima dari CodeGemma!")
    return response_container["text"]

# =====================================================================
# SIMULASI EKSEKUSI
# =====================================================================
if __name__ == "__main__":
    kode_uji = """
    def hitung_mundur(n)
        while n > 0
            print(n)
            n -= 1
        print("Mulai!")
    """

    print("=== 🛠️ MEMULAI SIMULASI CODE ROUTING ===")
    print(f"[*] Menguji potongan kode:\n{kode_uji}")
    
    # Jalankan System One (Penyaringan cepat)
    is_broken = triage_code_with_jev(kode_uji)
    print(f"[>] Hasil Analisis Jev (tev1): Apakah kode rusak? -> {is_broken}")

    # Jalankan Logika Pencabangan Routing
    if is_broken:
        print("\n[!] PERINGATAN: Kode terdeteksi rusak murni!")
        solusi_llm = fix_code_with_codegemma(kode_uji)
        print("\n=== 💡 HASIL PERBAIKAN DARI LLM MAIN ENGINE ===")
        print(solusi_llm)
        print("==================================================")
    else:
        print("\n[✓] Kode dinyatakan aman oleh Jev. Langsung dilempar ke compiler eksekusi.")