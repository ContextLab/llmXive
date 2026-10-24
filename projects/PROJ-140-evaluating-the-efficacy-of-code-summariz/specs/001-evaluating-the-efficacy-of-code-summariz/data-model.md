# Data Model: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

## 1. Entity‑Relationship Overview
| Entity | Primary Key | Key Attributes |
|--------|-------------|----------------|
| **Method** | `method_id` | `project_name`, `bug_id`, `source_code`, `ground_truth_line`, `context_code` |
| **Summary** | `summary_id` | `method_id` (FK), `condition` (`baseline`/`llm`/`rule`), `summary_text`, `generation_status` |
| **Participant** | `participant_id` (hashed) | `cohort`, `experience_years`, `dropout_status` |
| **Interaction** | `interaction_id` | `participant_id` (FK), `task_id`, `condition`, `timestamp_ms`, `selected_line`, `ground_truth_line`, `is_correct` (derived), **`fallback_status`** |

## 2. Data Flow
1. **Ingestion** – `download_defects4j.py` streams the verified Parquet dataset → `data/raw/defects4j.parquet`.  
2. **Method Extraction** – `generate_summaries.py` extracts methods → `data/processed/methods.csv`.  
3. **Summarization** –  
   - Baseline: `summary_text = null`.  
   - Rule‑based: srcML → `data/processed/summaries_rule.csv`.  
   - LLM: GPU escape hatch → `data/processed/summaries_llm.csv`.  
4. **Study Execution** –  
   - Simulated: `simulate_study.py` → `data/interaction_logs/simulated_logs.csv`.  
   - Real: Web UI writes `raw_logs.csv` → `pii.py` anonymizes → `data/interaction_logs/anonymized_logs.csv`.  
5. **Analysis** – `run_statistics.py` reads the anonymized interaction log + `methods.csv` → `data/analysis_results/results.json`.  

All intermediate files are validated against the JSON‑Schema contracts in `contracts/`.

## 3. Storage Formats
- **Raw Defects4J**: Parquet (`data/raw/defects4j.parquet`).  
- **Processed Tables**: CSV with headers (methods, summaries).  
- **Interaction Logs**: CSV (`participant_id,task_id,condition,timestamp_ms,selected_line,ground_truth_line,fallback_status`).  
- **Analysis Results**: JSON array of objects conforming to `contracts/analysis.schema.yaml`.  
- **Checksums**: SHA‑256 values stored in `data/checksums.txt`.

## 4. Anonymization Strategy
- Participant IDs are hashed with SHA‑256 + a secret salt (`data/.salt`, excluded from VCS).  
- No raw identifiers (names, emails, IPs) appear in any committed file.  
- Consent documents remain in `data/consent/` and are listed in `.gitignore`.  

---

