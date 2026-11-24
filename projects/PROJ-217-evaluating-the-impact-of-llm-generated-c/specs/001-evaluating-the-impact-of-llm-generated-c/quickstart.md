# Quickstart: Evaluating LLM-Generated Comments on Code Readability

## Prerequisites
1. Python 3.11 installed.  
2. CPU‑only environment (≤ 7 GB RAM).  
3. HuggingFace inference token with access to CodeLlama‑7B: `export HF_TOKEN="hf_..."`.  
4. Set deterministic seed: `export PROJECT_SEED=42`.  

## Step‑by‑Step Execution
| Step | Command | Description |
|------|---------|-------------|
| 0 | `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` | Isolated virtualenv with pinned dependencies. |
| 1 | `python -m src.data.download` | Download verified CodeSearchNet parquet (retry + SHA‑256 verification) **and convert it to `data/raw_snippets.jsonl`**, preserving original fields. |
| 2 | `python -m src.data.prepare` | Validate docstrings, filter, write `data/validated_snippets.jsonl`; excluded records → `data/excluded_records.json`; **write** `data/dataset_preparation.log` with total/valid/excluded counts. |
| 3 | `python -m src.utils.validate_environment` | FR‑006 environment & recruitment validation (Prolific API, consent PDF). Produces `recruitment_validation.log` and a boolean flag. |
| 4 | `python -m src.data.generate_comments` | Batch‑checkpointed LLM comment generation (truncation, retry, **fallback to deterministic placeholder comment** if API fails). Outputs `data/llm_comments.jsonl`, `data/generation_log.txt`, and `data/truncation_warnings.log`. |
| 5 | `python -m src.data.metrics` | Compute BLEU, ROUGE‑L, Sentence‑BERT similarity, **and** Flesch‑Kincaid Grade for all comment variants → `data/readability_metrics.csv`. |
| 6 | *(Collect human study data manually and place it at `data/human_study_responses.csv`)* | Must conform to `contracts/dataset.schema.yaml` after merge. |
| 7 | `python -m src.data.analysis` | Power analysis (repeated‑measures), one‑way ANOVA for time (required), mixed‑effects ANOVA for robustness, mixed‑effects logistic regression for accuracy, correlation analysis; outputs `results/analysis_results.json`, `results/fig_time_by_condition.pdf`, `results/fig_corr_heatmap.png`. |
| 8 | `pytest -q` | Contract validation of `merged_dataset.csv`, `analysis_results.json`, and checksum manifest. Any failure aborts CI. |
| 9 | `cat results/results_summary.md` | View the final human‑readable summary. |

## Expected Outputs
- `data/raw_snippets.jsonl`  
- `data/llm_comments.jsonl`  
- `data/readability_metrics.csv` (includes Flesch‑Kincaid Grade)  
- `data/merged_dataset.csv`  
- `results/analysis_results.json`  
- `results/fig_time_by_condition.pdf`  
- `results/fig_corr_heatmap.png`  
- `results/results_summary.md`  

## Re‑run Guidance
All scripts read `PROJECT_SEED` (default 42) and seed `random`, `numpy`, and `torch` deterministically. Downloads are checksum‑verified against the same canonical URLs on every run, ensuring reproducibility (Constitution I).

---


