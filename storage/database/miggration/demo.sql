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
