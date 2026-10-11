# Quickstart: Evaluating LLM‑Generated Comments on Code Readability

> **Goal**: Run the full end‑to‑end pipeline on a fresh GitHub Actions runner (or local machine) and obtain the final analysis tables and figures.

## Prerequisites
1. **Python 3.11** installed.  
2. **GitHub Actions runner** (CPU, ≤ 7 GB RAM) – no GPU required.  
3. **HuggingFace API token** with inference access. Export it as:
   ```bash
   export HF_TOKEN="hf_XXXXXXXXXXXXXXXX"
   ```
4. (Optional) **Git LFS** – not needed because all data are fetched via `datasets`.

## Step‑by‑Step

| Step | Command | Description |
|------|---------|-------------|
| 0️⃣  | `python -m venv .venv && source .venv/bin/activate` | Create isolated environment. |
| 0️⃣  | `pip install -r requirements.txt` | Install pinned dependencies. |
| 1️⃣  | `python -m src.data.download` | Download CodeSearchNet parquet files, verify checksums, produce `data/raw_snippets.jsonl` (includes `snippet_id`). |
| 2️⃣  | `python -m src.data.prepare` | Filter malformed docstrings, write `data/validated_snippets.jsonl` and `data/excluded_records.json`. |
| 3️⃣  | `python -m src.data.generate_comments` | Call HuggingFace API, apply retry/back‑off, produce `data/llm_comments.jsonl` (contains `snippet_id`). |
| 4️⃣  | `python -m src.data.metrics` | Compute BLEU, ROUGE‑L, Semantic similarity **for LLM comments only**, plus comment length & readability → `data/readability_metrics.csv`. |
| 5️⃣  | *(Obtain human study CSV manually and place it at `data/human_study_responses.csv`)* | Ensure columns match `contracts/dataset.schema.yaml`. |
| 6️⃣  | `python -m src.data.analysis` | Runs power analysis (targets 60 participants per condition), one‑way ANOVA, and correlation **using only LLM‑generated comments**; writes `results/` folder with JSON, CSV, PDF, PNG files. |
| 7️⃣  | `pytest -q` | Verify all contract schemas (`contracts/*.schema.yaml`) are satisfied. |
| 8️⃣  | `cat results/results_summary.md` | View the concise, reproducible report. |

## Expected Outputs
- `data/llm_comments.jsonl` – three comment variants per snippet (LLM, Human, None) with `snippet_id`.  
- `data/readability_metrics.csv` – BLEU, ROUGE‑L, Semantic similarity (null for non‑LLM rows), comment length, readability score.  
- `results/anova_results.json` – F‑statistic, p‑value for time & accuracy.  
- `results/correlations.csv` – Pearson *r* and Bonferroni‑corrected *p* for each LLM metric‑outcome pair.  
- `results/power_report.txt` – Achieved statistical power (target ≥ 0.80).  
- `results/fig_time_by_condition.pdf`, `results/corr_heatmap.png` – ready for paper inclusion.  

## Re‑run Guidance
- To reproduce exactly, set the random seed before any stochastic step:
  ```python
  import random, numpy as np, torch
  random.seed(42); np.random.seed(42); torch.manual_seed(42)
  ```
- All scripts read the seed from the environment variable `PROJECT_SEED` (default = 42).

---


