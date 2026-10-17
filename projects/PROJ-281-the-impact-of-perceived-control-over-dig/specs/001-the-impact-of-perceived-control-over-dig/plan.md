# Implementation Plan: The Impact of Perceived Control Over Digital Environments on Anxiety

**Branch**: `001-perceived-control-anxiety` | **Date**: 2026-10-17 | **Spec**: `specs/001-the-impact-of-perceived-control-over-dig/spec.md`  
**Input**: Feature specification from `/specs/001-the-impact-of-perceived-control-over-dig/spec.md`

## Summary
The pipeline will (1) download a public social‑media dataset, (2) filter non‑English and gibberish posts, (3) generate anxiety scores with a CPU‑only pretrained transformer, (4) compute a metadata‑only “perceived‑control” proxy, (5) merge the two streams, (6) run a Shapiro‑Wilk normality test, (7) select Pearson or Spearman correlation accordingly, (8) flag statistical significance (p < 0.05), (9) produce a scatter plot with a regression line, and (10) **verify** that the statistical workflow was executed correctly (T106). All steps run on a GitHub Actions free‑tier runner (≤2 CPU cores, ≤7 GB RAM, ≤6 h). Where the required dataset lacks a `filter_applied` field, the proxy will rely on `timestamp_regularity` alone, with an explicit limitation note (Constitution Principle VI).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets==2.19.0`, `transformers==4.44.0`, `scikit-learn==1.5.0`, `pandas==2.2.2`, `numpy==2.0.0`, `matplotlib==3.9.2`, `seaborn==0.13.2`, `langdetect==1.0.9`, `jsonschema==4.22.0`  
- **Storage**: CSV/JSON files under `data/` (raw, processed, analysis)  
- **Testing**: `pytest` with `pytest-cov`  
- **Target Platform**: Linux (GitHub Actions free tier)  
- **Project Type**: Computational research pipeline (CLI‑driven)  
- **Constraints**: CPU‑only inference (SC‑001), no text access during proxy extraction (SC‑002 / Principle VI), graceful error handling (SC‑003), ≤6 h runtime (SC‑004), fixed seeds in `code/config.py` (SC‑005).  

## Constitution Check

| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Deterministic `datasets.load_dataset` calls; `requirements.txt` pins versions; seeds fixed in `code/config.py`. |
| **II. Verified Accuracy** | No citation of unverified URLs; dataset is openly downloadable via HF API; limitations of missing `filter_applied` are flagged. |
| **III. Data Hygiene** | Raw download saved to `data/raw/social_media.csv` with SHA‑256 checksum; every transformation writes a new file; no in‑place edits. |
| **IV. Single Source of Truth** | `data/processed/final_analysis.csv` is the sole source for correlation statistics and plot; the manuscript will reference this file exclusively. |
| **V. Versioning Discipline** | All artifacts are hashed; the mechanical step records hashes in the project state file. |
| **VI. Measurement Independence** | `anxiety_scoring.py` accesses only the `text` column; `proxy_extractor.py` reads only metadata columns (`filter_applied`, `timestamp`). No cross‑modal leakage. |
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
| **0 – Research & Dataset Validation** | Identify an open HF dataset containing `text`, `timestamp`, `user_id`, and optionally `filter_applied`. Verify presence of required fields. | — | If `filter_applied` missing, proxy will rely on `timestamp_regularity` only (documented limitation). |
| **1 – Data Ingestion** | `data_ingestion.py` downloads `cardiffnlp/tweet_sentiment_extraction`, streams to `data/raw/social_media.csv`, computes SHA‑256 checksum, handles download failures gracefully. | AC‑001, AC‑002, SC‑003, T013 | Uses `datasets.load_dataset(..., streaming=True)` to stay within RAM. |
| **2 – Text Filtering & Anxiety Scoring** | • Load raw CSV.<br>• Filter non‑English posts via `langdetect` (confidence ≥ 0.8).<br>• Detect gibberish via length/entropy heuristics.<br>• Load CPU‑only RoBERTa‑base emotion model (`cardiffnlp/twitter-roberta-base-emotion`).<br>• Compute anxiety score = sum of probabilities for “anxiety”, “fear”, “sadness”.<br>• Record `confidence_score` = max class probability.<br>• Exclude rows with `confidence_score` < 0.6.<br>• Save to `data/processed/scoring_results.csv`. | AC‑003, AC‑004, T014b, T014c, T015, T016, T017 | Model inference set `device="cpu"`; batch size tuned for ≤2 CPU cores. |
| **3 – Control Proxy Extraction** | `proxy_extractor.py` reads only metadata columns, computes:<br>• `filter_flag` = 1 if `filter_applied` == True else 0 (if column exists).<br>• `timestamp_regularity` = 1 – (standard deviation of inter‑post intervals per user normalized to [0,1]).<br>• `control_proxy` = 0.6 × `filter_flag` + 0.4 × `timestamp_regularity`.<br>Writes `data/processed/proxy_results.csv`. | AC‑005, AC‑006, AC‑007, SC‑001, SC‑002, T021 | No access to `text` column; all operations are pure metadata. |
| **4 – Merge & Filter** | Join `scoring_results.csv` and `proxy_results.csv` on `post_id`; drop rows where `excluded` is True. Save merged file `data/processed/final_analysis.csv`. | — | Guarantees ≥95 % coverage of valid rows (AC‑003). |
| **5 – Statistical Testing** | `statistical_test.py` reads `final_analysis.csv`.<br>1. Run Shapiro‑Wilk on `anxiety_score` and `control_proxy` (separately).<br>2. If *both* p > 0.05 → Pearson; else → Spearman.<br>3. Compute correlation coefficient `r` and p‑value.<br>4. Set `is_significant = (p < 0.05)`.<br>5. Write JSON `data/processed/analysis_results.json` conforming to `contracts/analysis.schema.yaml`. | AC‑008, AC‑009, AC‑010, SC‑004, T106 (partial) | Normality test result stored as `normality_test_p_value`. |
| **6 – Visualization** | `plot_results.py` creates a scatter plot of `control_proxy` vs. `anxiety_score` with a regression line (linear fit for Pearson, monotonic fit for Spearman). Saves `data/processed/correlation_plot.png`. | AC‑011 | Plot generated before any manuscript step. |
| **7 – Reporting & Validation** | Generate `coverage_report.json` summarizing row counts, % excluded, checksum verification. Validate all JSON files against their schemas using `jsonschema`. | SC‑003, T018a | Failures abort pipeline with clear error messages. |
| **8 – **Statistical Verification (T106)** | `tests/integration/test_pipeline.py` re‑loads `analysis_results.json`, recomputes Shapiro‑Wilk on the original columns, checks that the recorded `correlation_method` matches the decision rule, and asserts that `is_significant` aligns with `p_value < 0.05`. Any mismatch triggers a test failure, ensuring AC‑008, AC‑009, AC‑010 are truly satisfied. | AC‑008, AC‑009, AC‑010, T106 | Provides the missing verification that the original reviewer flagged. |

## Compute Feasibility Note
- **CPU‑only**: All model inference performed with `device="cpu"`; no quantization or CUDA flags.
- **Memory**: Streaming load + chunked processing keeps peak RAM < 5 GB.
- **Runtime**: Benchmarks on a 2‑core GitHub Actions runner estimate ~1.5 h for 15 k posts; well under the 6 h limit. If the full dataset exceeds 30 k rows, a deterministic random sample (seeded) of 20 k rows will be taken, and the limitation will be documented in the final report.

---
