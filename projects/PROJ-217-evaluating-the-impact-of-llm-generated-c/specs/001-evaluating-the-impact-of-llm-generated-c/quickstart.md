# Quickstart: Evaluating LLM‑Generated Comments on Code Readability

> **Goal**: Run the full end‑to‑end pipeline on a fresh GitHub Actions runner (or local machine) and obtain the final analysis tables, figures, and reproducible summary report.

## Prerequisites
1. **Python 3.11** installed.  
2. **GitHub Actions runner** (CPU, ≤ 7 GB RAM) – no GPU required.  
3. **HuggingFace API token** with inference access. Export it:  
   ```bash
   export HF_TOKEN="hf_XXXXXXXXXXXXXXXX"
   ```
4. **Git LFS** not required; all data are fetched via the `datasets` library.

## Step‑by‑Step

| Step | Command | Description |
|------|---------|-------------|
| 0️⃣  | `python -m venv .venv && source .venv/bin/activate` | Create isolated environment. |
| 0️⃣  | `pip install -r requirements.txt` | Install pinned dependencies. |
| 0️⃣  | `export PROJECT_SEED=42` | Set deterministic random seed (default = 42). |
| 1️⃣  | `python -m src.data.download` | Download CodeSearchNet parquet files, verify SHA‑256 checksums, produce `data/raw_snippets.jsonl`. |
| 2️⃣  | `python -m src.data.prepare` | Filter malformed docstrings, write `data/validated_snippets.jsonl` and `data/excluded_records.json`. |
| 3️⃣  | `python -m src.data.generate_comments` | Call HuggingFace API, apply retry/back‑off, produce `data/llm_comments.jsonl`. |
| 4️⃣  | `python -m src.data.metrics` | Compute BLEU, ROUGE‑L, Semantic similarity (LLM‑only) + aux metrics → `data/readability_metrics.csv`. |
| 5️⃣  | `python -m src.utils.validate_recruitment` | Verify access to Prolific/Mturk API, check consent files, perform a dry‑run of participant creation (no real participants). |
| 6️⃣  | *(Obtain human study CSV manually and place it at `data/human_study_responses.csv`)* | Ensure columns match the schema in `contracts/dataset.schema.yaml`. |
| 7️⃣  | `python -m src.data.analysis` | Runs power analysis, one‑way ANOVA, and correlation (LLM‑only); writes `results/` folder with JSON, CSV, PDF, PNG files. |
| 8️⃣  | `pytest -q` | Verify **all** output files against both `contracts/dataset.schema.yaml` and `contracts/analysis.schema.yaml`. |
| 9️⃣  | `cat results/results_summary.md` | View the concise, reproducible report. |

## Expected Outputs
- `data/llm_comments.jsonl` – three comment variants per snippet (`llm`, `human`, `none`).  
- `data/readability_metrics.csv` – BLEU, ROUGE‑L, Semantic similarity (null for non‑LLM rows), comment length, readability score.  
- `results/anova_results.json` – F‑statistic & p‑value for time & accuracy.  
- `results/correlations.csv` – Pearson *r* and Bonferroni‑corrected *p* for each LLM metric‑outcome pair.  
- `results/power_report.txt` – Achieved statistical power (target ≥ 0.80).  
- `results/fig_time_by_condition.pdf`, `results/fig_corr_heatmap.png` – ready for paper inclusion.  
- `results/results_summary.md` – markdown summary that cites exact rows in `analysis_dataset.csv`.  

## Re‑run Guidance
- Set the random seed before any stochastic step to guarantee reproducibility:  
  ```python
  import random, numpy as np, torch, os
  seed = int(os.getenv("PROJECT_SEED", "42"))
  random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
  ```  
- All scripts read the seed from the environment variable `PROJECT_SEED` (default = 42).  

---


