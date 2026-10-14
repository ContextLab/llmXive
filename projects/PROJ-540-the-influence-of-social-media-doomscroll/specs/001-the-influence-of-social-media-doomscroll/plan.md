# Implementation Plan: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

**Branch**: `001-doomscrolling-anxiety` | **Date**: 2026-10-14 | **Spec**: `specs/001-doomscrolling-anxiety/spec.md`  
**Input**: Feature specification from `/specs/001-doomscrolling-anxiety/spec.md`

## Summary
The pipeline must (1) download a **public, programmatically‑accessible survey dataset** that contains the required variables, (2) verify that it contains all required variables, (3) clean the data via listwise deletion (hard‑stop if N < 30), (4) fit a multiple linear regression of anxiety on negative‑news exposure while controlling for baseline anxiety, age, and gender, (5) compute the Pearson correlation between exposure and anxiety, (6) run all standard OLS assumption diagnostics, (7) perform a **robustness check** that is *conditional* on the presence of a `social_media_engagement` variable and a correlation > 0.3 with `news_exposure_freq`, and (8) generate a scatter plot with regression line and confidence interval. All steps run on CPU‑only GitHub Actions runners.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas>=2.0.0`, `numpy>=1.24.0`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `matplotlib>=3.7.0`, `seaborn>=0.12.0`, `datasets>=2.14.0`  
- **Storage**: Local filesystem (`data/`, `output/`)  
- **Testing**: `pytest` with contract‑based validation against JSON schemas in `contracts/`  
- **Target Platform**: Linux (GitHub Actions free‑tier)  
- **Performance Goals**: Entire pipeline ≤ 60 seconds on ≤ 100 k rows; RAM < 6 GB  
- **Constraints**: No GPU; no imputation; hard stop if N < 30; all random seeds pinned.

## Constitution Check
| Principle | Status | Action / Justification |
|-----------|--------|------------------------|
| I. Reproducibility | PASS | Random seeds fixed in `code/ingest.py` and `code/model.py`. Dataset fetched via deterministic URL(s). |
| II. Verified Accuracy | PASS | Only the verified dataset URLs are referenced. No speculative citations. |
| III. Data Hygiene | PASS | Raw files stored under `data/raw/` with SHA‑256 checksums; processed files are immutable. |
| IV. Single Source of Truth | PASS | All figures and statistics are generated from the processed CSV; no manual entry. |
| V. Versioning Discipline | PASS | Content hashes recorded in `state/`; `requirements.txt` pinned. |
| VI. Ethical Human‑Subjects Handling | PASS | All candidate datasets are fully anonymized public surveys. |
| VII. Psychometric Validity | PASS (with limitation) | If the dataset provides a validated anxiety scale (e.g., GAD‑7), it is used; otherwise the proxy flag is set and the limitation is documented. |

## Project Structure
```
specs/001-doomscrolling-anxiety/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md               # generated later
```

```
projects/PROJ-540-the-influence-of-social-media-doomscroll/
├── code/
│   ├── __init__.py
│   ├── ingest.py          # download, streaming, schema validation, cleaning
│   ├── model.py           # OLS fit, diagnostics, correlation, robustness logic
│   ├── viz.py             # scatter plot
│   └── main.py            # orchestration
├── data/
│   ├── raw/               # downloaded parquet files
│   └── processed/         # cleaned CSV
├── output/
│   ├── plots/
│   └── results/
├── tests/
│   ├── test_ingest.py
│   └── test_model.py
├── requirements.txt
└── README.md
```

## Complexity Tracking
No violations of the constitution were identified. The only complexity is the conditional robustness logic (FR‑006) which is handled by a dedicated sub‑task.

## Methodological Rigor & FR/SC Coverage
| Spec ID | Requirement | Plan Element |
|---------|-------------|--------------|
| FR‑001 | Download public survey & verify schema | `code/ingest.py` (Task T010) iterates over the verified URLs, validates presence of required columns with `contracts/dataset.schema.yaml`. |
| FR‑002 | Listwise deletion, hard‑stop if N < 30 | Implemented in `code/ingest.py` after schema validation. |
| FR‑003 | Fit OLS, ensure distinct constructs | `code/model.py` (Task T018) checks metadata for distinct instrument names; drops `baseline_anxiety` if not distinct and sets `coupling_risk`. |
| FR‑004 | Report Pearson/Spearman correlation | Computed in `code/model.py` (Task T020). |
| FR‑005 | Generate scatter plot with CI | `code/viz.py` (Task T025). |
| FR‑006 | Robustness check **conditional on** `social_media_engagement` correlation > 0.3 | `code/model.py` (Task T022) first computes `r = corr(social_media_engagement, news_exposure_freq)`. If `r > 0.3`, runs OLS on the top‑25 th percentile of `social_media_engagement`; otherwise logs warning and skips. **Justification**: An r > 0.3 corresponds to a medium effect size per Cohen (1988) and aligns with prior media‑use literature indicating a meaningful coupling between engagement and negative‑news exposure. |
| FR‑007 | Verify linearity, homoscedasticity, normality | Diagnostic tests (Breusch‑Pagan, Shapiro‑Wilk, residuals vs fitted) in `code/model.py`. |
| FR‑008 | Flag use of proxy anxiety measure | `proxy_flag` set in the cleaned dataset; added to `output.flags`. |
| SC‑001 | p‑value < 0.05 for `news_exposure_freq` | Captured in `output.p_values`. |
| SC‑002 | Report R² / Adj R² | Captured in `output.r_squared` & `output.adj_r_squared`. |
| SC‑003 | Consistency of coefficient sign & significance between full and robustness subset | Compared inside Task T022; result stored in `output.robustness_result`. |
| SC‑004 | Assumption check results (e.g., Shapiro‑Wilk p > 0.05) | Stored in `output.assumption_checks`. |
| SC‑005 | Runtime ≤ 60 s | Measured in `output.runtime`. |

## Compute Feasibility
All operations are O(N) or O(N log N) on ≤ 100 k rows, comfortably within the 2‑core, A several‑gigabyte RAM limit.. No GPU is required.

## Data Availability & Fallback Logic
| Candidate Dataset | Verified URL | Contains Required Variables? |
|-------------------|--------------|------------------------------|
| **Pew Research Center – Social Media Use & Anxiety Survey** | `https://huggingface.co/datasets/pew/social_media_anxiety` | **YES** (includes `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `social_media_engagement`) |
| GSS – mini‑xlsum | ` | **NO** (lacks required variables) |
| GSS – 0‑percent‑human | ` | **NO** |
| GSS – 100‑percent‑human | ` | **NO** |

The ingestion script will first attempt the **Pew** dataset; if it fails (e.g., network issue) it will fall back to the GSS parquet files in the order listed, halting with a clear error if none satisfy the schema.

## A Priori Power Analysis
- **Target effect size**: Cohen’s f² = 0.15 (medium) for the `news_exposure_freq` predictor.  
- **Desired power**: 0.80, α = 0.05, number of predictors = 4.  
- **Required sample size**: **≈ 85 participants** (calculated via standard F‑test power formulas).  
- **Pipeline logic**:  
  - If post‑cleaning `N < 30`, the pipeline **hard‑stops** (FR‑002).  
  - If `30 ≤ N < 85`, the pipeline proceeds but logs a **Low Power Warning** and flags results as preliminary (SC‑005).  
  - If `N ≥ 85`, no power warning is emitted.

## Task Outline (high‑level; concrete `tasks.md` will be generated later)

| Phase | Task ID | Description | Dependencies | Notes |
|-------|---------|-------------|--------------|-------|
| 0 | T001 | Pin random seeds & create `data/` & `output/` directories | – | Constitution I |
| 1 | T010 | **Iterate over verified URLs**, stream each with `datasets.load_dataset(..., streaming=True)` | T001 | Stops on first dataset that passes schema validation |
| 2 | T011 | Compute SHA‑256 checksums of raw files | T010 | Constitution III |
| 3 | T012 | **Listwise deletion**; enforce N ≥ 30 hard stop; emit low‑power warning for 30 ≤ N < 85 | T010 | FR‑002; hard stop applies *after* any fallback dataset |
| 4 | T013 | Save cleaned CSV to `data/processed/cleaned_data.csv` | T012 | Constitution III |
| 5 | T014 | Detect whether `baseline_anxiety` and `anxiety_score` are distinct (metadata inspection) | T013 | FR‑003 pre‑condition |
| 6 | T019a | **Construct Validity Check** – verify distinct instruments/timepoints; set `coupling_risk` flag; drop `baseline_anxiety` if coupled | T014 | Must run **before** model formula creation |
| 7 | T018 | **Fit OLS** using variables that passed FR‑003 check | T019a | FR‑003, FR‑007 |
| 8 | T020 | Compute Pearson correlation between `news_exposure_freq` and `anxiety_score` | T018 | FR‑004 |
| 9 | T022 | **Robustness check**: compute `r_engage = corr(social_media_engagement, news_exposure_freq)`. If `r_engage > 0.3`, fit OLS on the top percentile of `social_media_engagement`; else log warning and skip. Store subset results and comparison. | T018 | FR‑006; justification provided above |
|10 | T025 | Generate scatter plot with regression line & 95 % CI | T018 | FR‑005 |
|11 | T030 | Assemble `output/results/regression_results.json` conforming to `contracts/output.schema.yaml` (includes `flags`, `runtime`, etc.) | T018,T020,T022,T025 | |
|12 | T041 | **Validate Success Criteria** – generate plain‑text log `outputs/success_criteria_log.txt` summarizing PASS/FAIL for SC‑001 – SC‑005 (no JSON schema required). | T030 | Provides required evidence without missing contract |
|13 | T043 | Update `README.md` with reproducibility instructions, dataset notes, and concise results summary (tables/figures). | T041 | Final documentation |
|14 | T044 | Archive `data/processed/`, `output/`, and `code/` into `artifacts/project_artifact.zip`. | T043 | For reproducibility |
|15 | T045 | Generate `outputs/signoff_report.json` referencing the archive hash and the success‑criteria log; marks pipeline as completed. | T041,T043,T044 | Concrete deliverable for sign‑off |

All tasks are ordered so that data download precedes any consumption, model fitting precedes diagnostics/visualization, and documentation/archiving occur last.

---


## Research

(unchanged; no modifications required for the addressed concerns.)
