# Quickstart: Evaluating the Impact of Code Generation on Code Review Time

## Prerequisites
- **Python 3.11** (or newer)  
- **Git** (to clone the repository)  
- No GPU is required; the pipeline runs entirely on CPU using the CodeLlama‑7B‑4bit‑GGUF model.  

## 1. Clone the Repository
```bash
git clone <REPO_URL>
cd projects/PROJ-302-evaluating-the-impact-of-code-generation
```

## 2. Set Up a Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Verify the Environment
```bash
python -c "import pandas, datasets, torch, transformers, radon; print('All deps OK')"
```

## 4. Run the Full End‑to‑End Pipeline
```bash
python code/main.py --full-run
```
The script performs the following ordered stages (each writes a deterministic artifact):
1. **Data Acquisition** (`data_acquisition.py`) – streams the three verified PR parquet files, filters by stars ≥ 1 000 and PR count ≥ 100, writes `data/raw/*.parquet` and records SHA‑256 checksums.  
2. **Prompt Engineering** (`prompt_engineering.py`) – extracts NL prompts from commit messages, writes `data/processed/intent_prompts.json`.  
3. **Synthetic Generation** (`synthetic_generation.py`) – creates *prompt‑only* and *context‑based* cohorts with CodeLlama‑7B‑4bit‑GGUF; enforces ≤ 30 s per snippet, 3 retries, AST validity ≥ 95 %; writes `data/synthetic/llm_snippets.jsonl`.  
4. **Feature Extraction** (`feature_extraction.py`) – computes LOC, radon cyclomatic complexity, CI build time, and all‑MiniLM‑L6‑v2 embeddings + cosine similarity; writes `features.parquet`.  
5. **Outcome Prediction** (`outcome_prediction.py`) – trains a regression model on human PRs and predicts `review_effort_duration` for LLM‑generated PRs, writing predictions back to the merged dataset.  
6. **Propensity‑Score Matching** (`matching.py`) – matches human and LLM PRs on the five covariates, generates `matched_pairs.parquet` and `covariate_balance.json`.  
7. **Statistical Analysis** (`analysis.py`) – Shapiro‑Wilk, test selection, compute p‑value, effect size, `passed` flag; validates against `contracts/test_result.schema.yaml`.  
8. **Sensitivity Analysis** (`sensitivity.py`) – quartile sweeps, writes `sensitivity_summary.json`.  
9. **Visualization** (`visualization.py`) – box plot & CDF PNGs for `total_review_duration`.  
10. **Report Generation** (`report_generator.py`) – assembles HTML and PDF (`reports/analysis_report.pdf`).  
11. **Runtime Measurement** (`runtime.py`) – records stage timings, fails if total > 6 h, writes `runtime_report.json`.

## 5. Verify the Outputs
| Artifact | Expected Location | What to Check |
|---|---|---|
| Raw streamed PRs | `data/raw/` | Parquet files exist; SHA‑256 matches state file. |
| Synthetic snippets | `data/synthetic/llm_snippets.jsonl` | ≥ 95 % `is_valid_syntax` = true (see `syntax_validity.json`). |
| Covariate Balance Report | `data/reports/covariate_balance.json` | All SMD < 0.1. |
| Statistical Results | `data/reports/statistical_results.json` | Conforms to `contracts/test_result.schema.yaml`; `passed` reflects p < 0.05. |
| Sensitivity Summary | `data/reports/sensitivity_summary.json` | ≥ 80 % subsets with p < 0.05. |
| Visualisations | `data/reports/boxplot.png`, `data/reports/cdf.png` | PNG files open without error. |
| Final Report | `reports/analysis_report.pdf` | PDF includes tables, figures, and provenance metadata. |
| Runtime Report | `data/reports/runtime_report.json` | Total wall‑time ≤ 21600 seconds (6 h). |

## 6. Troubleshooting
- **GitHub API rate limits**: Export a personal access token: `export GITHUB_TOKEN=your_token`.  
- **Memory errors**: Reduce streaming batch size (`--batch-size 200`) or limit PR count (`--max-prs 5000`).  
- **Matching failure**: Inspect `data/reports/matching_failure_report.json` for covariates with high SMD; you may increase the caliper or drop the most imbalanced covariate and re‑run.  
- **LLM generation timeout**: The script retries up to 3 times; persistent failures are logged and the corresponding commit is excluded.  
- **Runtime exceeds 6 h**: Review `runtime_report.json` for the longest stage; consider reducing the number of synthetic snippets (`--max-snippets`) or using a smaller subset of repos.

## 7. Reproducibility Guarantees
- All random seeds are fixed (`utils.set_seed(42)`).  
- External datasets are fetched from the exact URLs listed in this document; their SHA‑256 checksums are recorded.  
- The CodeLlama model version and generation parameters are stored alongside each snippet.  
- Every figure and statistic in the PDF can be traced back to a single row in a Parquet/JSON artifact.

Enjoy your reproducible study!

---



