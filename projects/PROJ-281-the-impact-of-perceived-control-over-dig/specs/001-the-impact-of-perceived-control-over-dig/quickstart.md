# Quickstart Guide: The Impact of Perceived Control Over Digital Environments on Anxiety

## Overview
A reproducible, CPU‑only pipeline that downloads a public tweet dataset, scores anxiety, extracts a metadata‑based control proxy, runs a statistically rigorous correlation analysis, and visualizes the result.

## Prerequisites
- Python 3.11+
- `pip`
- At least **7 GB** RAM available
- ≤ 6 h uninterrupted runtime (GitHub Actions free tier)

## Installation
```bash
git clone <repository-url>
cd llmXive-proj-281
pip install -r requirements.txt
```

## Running the Full Pipeline
```bash
python code/main.py
```
This executes, in order:
1. Data ingestion & checksum (`data_ingestion.py`)
2. Language/gibberish filtering & anxiety scoring (`anxiety_scoring.py`)
3. Control proxy extraction (`proxy_extractor.py`)
4. Merge & confidence filtering
5. Shapiro‑Wilk test, correlation selection, significance flag (`statistical_test.py`)
6. Scatter plot with regression line (`plot_results.py`)

**Expected runtime**: ~1.5 h for 20 k posts on a 2‑core runner.  
**Peak memory**: < 5 GB.

## Running Individual Stages (debugging)
```bash
python code/services/data_ingestion.py          # Stage 1
python code/services/anxiety_scoring.py         # Stage 2
python code/services/proxy_extractor.py         # Stage 3
python code/analysis/statistical_test.py        # Stage 5
python code/viz/plot_results.py                 # Stage 6
```

## Output Files
| File | Description |
|------|-------------|
| `data/raw/social_media.csv` | Raw download (checksum recorded). |
| `data/processed/preprocessed_text.csv` | English, non‑gibberish tweets. |
| `data/processed/scoring_results.csv` | Anxiety scores & confidence. |
| `data/processed/proxy_results.csv` | Control proxy values. |
| `data/processed/final_analysis.csv` | Merged dataset used for statistics. |
| `data/processed/analysis_results.json` | Correlation method, coefficient, p‑value, significance flag, normality p‑value, sample size, confidence threshold (conforms to `contracts/analysis.schema.yaml`). |
| `data/processed/correlation_plot.png` | Scatter plot with regression line. |
| `data/processed/coverage_report.json` | Row‑count and checksum audit (conforms to `contracts/dataset.schema.yaml`). |
| `data/processed/profiling_report.json` | Runtime & memory usage vs. SC‑004 limits. |

## Validation & Testing
```bash
pytest tests/ -v --cov=code
```
Key integration tests verify:
- Presence and schema compliance of all JSON/CSV artifacts.
- Correct execution of Shapiro‑Wilk, method selection, and `is_significant` flag (addresses AC‑008 – AC‑010).
- Graceful handling of download failures (SC‑003).

## Troubleshooting
- **Missing dataset URL**: The required dataset lacks a verified URL; the pipeline will attempt to download it via `datasets.load_dataset`. If the download fails, the run aborts with a clear error (no synthetic data generated).  
- **Runtime exceeds 6 h**: The pipeline will automatically fall back to a deterministic random sample of 20 k rows and log the limitation in `coverage_report.json`.  
- **Memory errors**: Ensure streaming mode is active; the pipeline processes data in 1 k‑row chunks.

## Next Steps
1. Review `analysis_results.json` for the correlation statistics.  
2. Inspect `correlation_plot.png`.  
3. Incorporate the figures and numbers into the manuscript (single source of truth).  

---
