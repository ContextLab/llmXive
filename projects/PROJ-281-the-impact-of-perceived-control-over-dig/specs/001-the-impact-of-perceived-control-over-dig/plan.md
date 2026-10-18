# Implementation Plan: The Impact of Perceived Control Over Digital Environments on Anxiety

**Branch**: `001-perceived-control-anxiety` | **Date**: 2026-10-17 | **Spec**: `specs/001-the-impact-of-perceived-control-over-dig/spec.md`  
**Input**: Feature specification from `/specs/001-the-impact-of-perceived-control-over-dig/spec.md`

## Summary
The pipeline will (1) download the open HuggingFace dataset `cardiffnlp/tweet_sentiment_extraction` (which contains `text`, `timestamp`, `user_id`, and optionally `filter_applied`), (2) filter non‑English and gibberish posts, (3) generate anxiety scores with a CPU‑only RoBERTa‑base emotion model, (4) compute a metadata‑only “perceived‑control” proxy using `filter_applied` and `timestamp_regularity` (without accessing text), (5) merge the two streams, (6) fit an OLS regression, **run a Shapiro‑Wilk test on the regression residuals** to assess normality, (7) select **Pearson** correlation if residuals are normal, otherwise **Spearman** (with user‑level de‑meaning to control for confounding), (8) flag statistical significance (p < 0.05), (9) perform a **post‑hoc power analysis**, (10) generate a scatter plot with regression line, (11) **verify** that the statistical workflow (residual normality test, method choice, significance flag, power estimate) was executed correctly (T106), and (12) report all results. All steps run on a GitHub Actions free‑tier runner (≤2 CPU cores, ≤7 GB RAM, ≤6 h). If the dataset exceeds the runtime budget, a deterministic random sample of a suitably sized subset of rows is taken and the limitation is documented.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets==2.19.0`, `transformers==4.44.0`, `scikit-learn==1.5.0`, `pandas==2.2.2`, `numpy==2.0.0`, `matplotlib==3.9.2`, `seaborn==0.13.2`, `langdetect==1.0.9`, `statsmodels==0.14.2`, `jsonschema==4.22.0`  
- **Storage**: CSV/JSON files under `data/` (raw, processed, analysis)  
- **Testing**: `pytest` with `pytest-cov`  
- **Target Platform**: Linux (GitHub Actions free tier)  
- **Constraints**: CPU‑only inference (SC‑001), no text access during proxy extraction (SC‑002 / Principle VI), graceful error handling (SC‑003), ≤6 h runtime (SC‑004), fixed seeds in `code/config.py` (SC‑005).  

## Constitution Check

| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Deterministic `datasets.load_dataset` calls; `requirements.txt` pins versions; seeds fixed in `code/config.py`. |
| **II. Verified Accuracy** | **Dataset citation**: <https://huggingface.co/datasets/cardiffnlp/tweet_sentiment_extraction> (verified HuggingFace repository). **Model citation**: <https://huggingface.co/cardiffnlp/twitter-roberta-base-emotion> (verified HuggingFace repository). |
| **III. Data Hygiene** | Raw download saved to `data/raw/social_media.csv` with SHA‑256 checksum; every transformation writes a new file; no in‑place edits. |
| **IV. Single Source of Truth** | `data/processed/final_analysis.csv` is the sole source for correlation statistics and plot; the manuscript will reference this file exclusively. |
| **V. Versioning Discipline** | All artifacts are hashed; the mechanical step records hashes in the project state file. |
| **VI. Measurement Independence** | `anxiety_scoring.py` accesses only the `text` column; `proxy_extractor.py` reads only metadata columns (`filter_applied`, `timestamp`, `user_id`). No cross‑modal leakage. |
| **VII. Operationalization of Digital Agency** | Control proxy computed as deterministic function of `filter_applied` (binary) and `timestamp_regularity` (continuous), implemented in `code/services/proxy_extractor.py`. |

## Project Structure
```text
specs/001-the-impact-of-perceived-control-over-dig/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── analysis.schema.yaml
    └── dataset.schema.yaml

code/
├── __init__.py
├── config.py                # seeds, paths, runtime limits
├── main.py                  # orchestrates the full pipeline
├── services/
│   ├── __init__.py
│   ├── data_ingestion.py    # T013
│   ├── anxiety_scoring.py   # T014b, T014c, T015, T016, T017
│   └── proxy_extractor.py   # T021
├── analysis/
│   ├── __init__.py
│   └── statistical_test.py  # AC‑008‑AC‑010, produces analysis_results.json
└── viz/
    └── plot_results.py      # AC‑011

tests/
├── unit/
│   ├── test_data_ingestion.py
│   ├── test_anxiety_scoring.py
│   └── test_proxy_extractor.py
└── integration/
    └── test_pipeline.py      # includes T106 verification

requirements.txt
```

## Phase Breakdown & Mapping to Acceptance Criteria / System Constraints

| Phase | Tasks | Mapped AC / SC | Notes |
|-------|-------|----------------|-------|
| **0 – Dataset Selection & Validation** | Identify the open HF dataset `cardiffnlp/tweet_sentiment_extraction`. Verify programmatically that it contains `text`, `timestamp`, `user_id`, and optionally `filter_applied`. | AC‑001, AC‑005, AC‑006, SC‑003 | If `filter_applied` is missing, `filter_flag` defaults to `False` and the proxy relies solely on `timestamp_regularity` (documented limitation per Principle VI). |
| **1 – Data Ingestion** | `data_ingestion.py` downloads the dataset via `datasets.load_dataset(..., streaming=True)`, streams to `data/raw/social_media.csv`, computes SHA‑256 checksum, handles download failures gracefully. | AC‑001, AC‑002, SC‑003, T013 | Streaming keeps RAM < 5 GB. |
| **2 – Text Filtering & Anxiety Scoring** | • Load raw CSV.<br>• Filter non‑English posts using `langdetect` with confidence ≥ 0.8.<br>• Detect gibberish via length/entropy heuristics.<br>• Load CPU‑only RoBERTa‑base emotion model (`cardiffnlp/twitter-roberta-base-emotion`).<br>• Compute anxiety score = sum of probabilities for “anxiety”, “fear”, “sadness”.<br>• Record `confidence_score` = max class probability.<br>• Exclude rows with `confidence_score` < 0.6.<br>• Save to `data/processed/scoring_results.csv`. | AC‑003, AC‑004, T014b, T014c, T015, T016, T017 | Model inference runs on `device="cpu"`; batch size tuned for ≤2 CPU cores. Construct‑validity justification added in Research. |
| **3 – Control Proxy Extraction** | `proxy_extractor.py` reads only metadata columns, computes:<br>• `filter_flag` = 1 if `filter_applied` == True else 0 (if column exists).<br>• `timestamp_regularity` = 1 – (standard deviation of inter‑post intervals per user normalized to [0,1]).<br>• `control_proxy` = 0.6 × `filter_flag` + 0.4 × `timestamp_regularity` (if `timestamp` missing, set `timestamp_regularity` = 0 and document).<br>Writes `data/processed/proxy_results.csv`. | AC‑005, AC‑006, AC‑007, SC‑001, SC‑002, T021 | No access to `text`. |
| **4 – Merge & Filter** | Join `scoring_results.csv` and `proxy_results.csv` on `post_id`; drop rows where `excluded` is True. Save merged file `data/processed/final_analysis.csv`. | — | Guarantees ≥95 % coverage of valid rows (AC‑003). |
| **5 – Statistical Testing** | `statistical_test.py` reads `final_analysis.csv`.<br>1. Fit OLS regression `anxiety_score ~ control_proxy` (using `statsmodels`).<br>2. Extract residuals and run **Shapiro‑Wilk test on the residuals**.<br>3. If residuals are normal (p > 0.05) → **Pearson**; otherwise → **Spearman** (with user‑level de‑meaning to control for user‑specific confounds).<br>4. Compute correlation coefficient `r` and p‑value.<br>5. Set `is_significant = (p < 0.05)`.<br>6. Perform a **post‑hoc power analysis** (using `statsmodels.stats.power`) and record achieved power.<br>7. Write JSON `data/processed/analysis_results.json` conforming to `contracts/analysis.schema.yaml`. | AC‑008, AC‑009, AC‑010, SC‑004, T106 (expanded) | Normality test now on residuals; power analysis added; confounding control added. |
| **6 – Visualization** | `plot_results.py` creates a scatter plot of `control_proxy` vs. `anxiety_score` with a regression line (linear fit for Pearson, monotonic fit for Spearman). Saves `data/processed/correlation_plot.png`. | AC‑011 | Plot generated before manuscript step. |
| **7 – Reporting & Validation** | Generate `coverage_report.json` summarizing row counts, % excluded, checksum verification. Validate all JSON/CSV artifacts against their schemas using `jsonschema`. | SC‑003, T018a | Failures abort pipeline with clear messages. |
| **8 – Statistical Verification (T106)** | `tests/integration/test_pipeline.py` re‑loads `analysis_results.json` and `final_analysis.csv`, **re‑computes** the OLS regression, **re‑runs** the Shapiro‑Wilk test on residuals, **verifies** that the stored `correlation_method` matches the decision rule, **checks** that `is_significant` equals `(p_value < 0.05)`, and **confirms** that the reported `achieved_power` matches the post‑hoc calculation. Any mismatch fails the test, guaranteeing AC‑008, AC‑009, AC‑010 are truly satisfied. |
| **9 – Runtime Guard** | If total runtime exceeds 6 h (SC‑004) the pipeline automatically switches to a deterministic random sample of 20 k rows (seeded) and logs the limitation in `coverage_report.json`. | SC‑004 | Ensures compliance with the runtime budget. |

## Compute Feasibility Note
- **CPU‑only**: All model inference performed with `device="cpu"`; no quantization or CUDA.
- **Memory**: Streaming load + chunked processing keeps peak RAM < 5 GB.
- **Runtime**: Benchmarks on a GitHub Actions free‑tier runner estimate total runtime on the order of a few hours for 20 k rows. If the full dataset exceeds 30 k rows, a deterministic random sample of 20 k rows (seeded) is taken and the limitation is logged in `coverage_report.json`.

---


