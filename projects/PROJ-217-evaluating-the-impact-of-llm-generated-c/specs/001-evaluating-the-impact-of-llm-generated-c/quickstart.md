# Quickstart: Evaluating LLM-Generated Comments on Code Readability

## Prerequisites
1. Python 3.11.
2. CPU‑only runner (≤ 7 GB RAM); no GPU required.
3. HuggingFace token with inference access: `export HF_TOKEN="hf_..."`.
4. `export PROJECT_SEED=42`.

## Step‑by‑Step
| Step | Command | Description |
|------|---------|-------------|
| 0 | `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` | Isolated env with pinned deps |
| 1 | `python -m src.data.download` | Download verified CodeSearchNet parquet (retry + column‑tolerant mapping), verify SHA‑256 → `data/raw_snippets.jsonl` |
| 2 | `python -m src.data.prepare` | Validate docstrings, filter, and write `data/validated_snippets.jsonl`; excluded records → `data/excluded_records.json` with `reason` |
| 3 | `python -m src.utils.validate_environment` | FR‑006 environment/recruitment validation (Prolific API check, consent PDF load); boolean success flag + `recruitment_validation.log` |
| 4 | `python -m src.data.generate_comments` | HF Inference API (retry/backoff, 2048‑token truncation) → `data/llm_comments.jsonl` |
| 5 | `python -m src.data.metrics` | BLEU, ROUGE‑L, Sentence‑BERT + aux metrics for **all comment variants** → `data/readability_metrics.csv` |
| 6 | *(place human study CSV at `data/human_study_responses.csv`)* | Must conform to `contracts/dataset.schema.yaml` **after** merging (see Step 7). |
| 7 | `python -m src.data.analysis` | Power analysis, mixed‑effects ANOVA, mixed logistic regression, correlation (aggregated per snippet) → `results/analysis_results.json`, figures in `results/` |
| 8 | `pytest -q` | Contract validation of all outputs (`merged_dataset.csv`, `analysis_results.json`, etc.) |
| 9 | `cat results/results_summary.md` | Final report |

## Expected Outputs
- `data/llm_comments.jsonl`, `data/readability_metrics.csv`, `data/merged_dataset.csv`
- `results/analysis_results.json`, `results/fig_time_by_condition.pdf`, `results/fig_corr_heatmap.png`, `results/results_summary.md`

## Re‑run Guidance
All scripts read `PROJECT_SEED` (default 42) and seed `random`, `numpy`, `torch` deterministically. Downloads are checksum‑verified against the same canonical verified URLs on every run.

---

