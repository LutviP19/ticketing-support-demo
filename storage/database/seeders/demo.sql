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



SELECT 
	jsonb_object_agg(
		jq.question_key, 
		jsonb_build_object(
			'type', jq.decision_type,
			'instructions', jq.instructions,
			'criteria', CASE 
				WHEN jq.decision_type = 'noul' THEN NULL
				WHEN jq.decision_type = 'score' THEN (
					SELECT jsonb_agg(jc.option_description ORDER BY jc.sort_order)
					FROM jev_criteria jc WHERE jc.question_id = jq.id
				)
				ELSE (
					SELECT jsonb_object_agg(jc.option_key, jc.option_description)
					FROM jev_criteria jc WHERE jc.question_id = jq.id
				)
			END
		)
	) AS formatted_questions
FROM jev_questions jq
WHERE jq.decision_set_id = 1;

