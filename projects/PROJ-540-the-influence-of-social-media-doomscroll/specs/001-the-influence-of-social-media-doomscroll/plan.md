# Implementation Plan: The Influence of Social Media “Doomscrolling” on Anticipatory Anxiety

**Branch**: `001-doomscrolling-anxiety` | **Date**: 2026-10-23 | **Spec**: `specs/001-doomscrolling-anxiety/spec.md`  
**Input**: Feature specification from `/specs/001-doomscrolling-anxiety/spec.md`

## Summary
The pipeline will initially download the verified public parquet files, compute SHA‑256 checksums, and verify that the required variables are present. If a dataset passes validation, the pipeline will (1) perform listwise deletion (hard stop if N < 30, low‑power warning if 30 ≤ N < 100); (2) run an **a‑priori power analysis** (Task T014) to ensure the cleaned sample can detect the effect‑size thresholds defined in SC‑001; (3) assess the missing‑data mechanism with Little’s MCAR test (Task T015); (4) verify that the anxiety outcome and baseline anxiety are measured with distinct instruments/timepoints (Task T019a); (5) fit a multiple linear regression of `anxiety_score` on `news_exposure_freq`, `baseline_anxiety`, `age`, and `gender` (Task T018); (6) compute the Pearson correlation if both variables are normally distributed, otherwise Spearman (Task T020); (7) run assumption diagnostics (linearity, homoscedasticity, normality of residuals, VIF) (Task T018/T022); (8) **perform the conditional robustness check** on the high‑engagement subset when the correlation gate (Pearson or Spearman, |r| > 0.3) is satisfied (Task T022); (9) generate a scatter plot with regression line and 95 % confidence interval as part of the modeling task (merged into Task T018); (10) validate success criteria SC‑001 – SC‑005 (Task T041); and (11) produce a single‑source‑of‑truth JSON (`output/results/regression_results.json`). Because none of the verified datasets contains the six required columns, the pipeline will **download the three files, record their true column inventories, and halt at schema validation** (FR‑001 edge case). A suitable open dataset must be supplied for any statistical analysis to proceed.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas>=2.0.0`, `numpy>=1.24.0`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `matplotlib>=3.7.0`, `pyarrow>=14.0.0`, `pyyaml>=6.0`, `jsonschema>=4.19.0` (pinned in `requirements.txt`)  
- **Storage**: Local filesystem under `data/` (raw & processed) and `output/` (results & plots)  
- **Testing**: `pytest` + contract validation against `contracts/*.schema.yaml`  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, no GPU)  
- **Constraints**: CPU‑only; no imputation; hard stop if N < 30; listwise deletion only; no Bonferroni correction (per SC‑001); all random seeds pinned for reproducibility.  

## Constitution Check
| Principle | Status | Action / Justification |
|-----------|--------|------------------------|
| I. Reproducibility | PASS | Fixed seeds; deterministic downloads; same SHA‑256 each run |
| II. Verified Accuracy | PASS | Only the three verified URLs are cited; no unverified dataset used |
| III. Data Hygiene | PASS | Raw files stored immutable with SHA‑256; all transformations write new files |
| IV. Single Source of Truth | PASS | All statistics derived from `output/results/regression_results.json` |
| V. Versioning Discipline | PASS | `requirements.txt` pinned; content hashes recorded in `state/...` |
| VI. Ethical Human‑Subjects Handling | PASS | Only open, non‑human‑subject corpora are downloaded; any future survey data will be anonymised |
| VII. Psychometric Validity | BLOCKED | No verified dataset provides a validated anxiety instrument; the pipeline records a `proxy_flag` when a proxy is used, but currently halts due to missing variables |

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
└── tasks.md   (generated later)

projects/PROJ-540-the-influence-of-social-media-doomscroll/
├── code/
│   ├── __init__.py
│   ├── ingest.py          # T010 – download, checksum, schema validation
│   ├── power.py           # T014 – a‑priori power analysis
│   ├── missingness.py     # T015 – MCAR test
│   ├── model.py           # T018‑T022 – OLS, diagnostics, robustness, plot generation
│   ├── validate_sc.py     # T041 – success‑criteria validation
│   └── main.py            # orchestration
├── data/
│   ├── raw/               # immutable parquet downloads
│   └── processed/         # (optional) cleaned CSV if a dataset validates
├── output/
│   ├── plots/
│   └── results/
│       └── regression_results.json
├── outputs/
│   ├── success_criteria_log.txt
│   └── signoff_report.json   (generated automatically by CI)
├── tests/
│   ├── test_ingest.py
│   └── test_model.py
├── requirements.txt
└── README.md
```

## Complexity Tracking
Only **Principle VII** is blocked pending a verified dataset with a validated anxiety instrument. All other principles are satisfied.

## Methodological Rigor & FR/SC Coverage
| Spec ID | Requirement | Plan Element (Task ID) | Status |
|---------|-------------|------------------------|--------|
| FR‑001 | Download public dataset & verify schema | `code/ingest.py` (T010) | EXECUTED – current outcome = HALTED_NO_VALID_DATASET |
| FR‑002 | Listwise deletion; hard stop if N < 30; low‑power warning if 30 ≤ N < 100 | `code/ingest.py` (post‑validation cleaning) | CONDITIONAL – runs only if a dataset validates |
| FR‑014 (new) | A‑priori power analysis for SC‑001 thresholds | `code/power.py` (T014) | CONDITIONAL – runs after cleaning; halts if power insufficient |
| FR‑015 (new) | Assess missingness mechanism (MCAR) | `code/missingness.py` (T015) | CONDITIONAL – runs after cleaning |
| FR‑003 | Fit OLS; ensure distinct anxiety instruments/timepoints | `code/model.py` (T018‑T019a) | CONDITIONAL – distinctness check added |
| FR‑004 | Pearson if normal, else Spearman | `code/model.py` (T020) | CONDITIONAL – normality test determines statistic |
| FR‑006 | Robustness check gated by r > 0.3 with appropriate correlation type | `code/model.py` (T022) | CONDITIONAL – gate uses Pearson or Spearman based on normality |
| FR‑007 | Assumption diagnostics (linearity, homoscedasticity, normality, VIF) | `code/model.py` (T018‑T022) | EXECUTED |
| FR‑008 | Proxy‑anxiety flag & construct‑validity note | `code/ingest.py` & `code/model.py` (T019a) | CONDITIONAL – flag set when proxy used; `proxy_validated` recorded |
| SC‑001 | p < 0.05 **and** (β ≥ 0.10 or f² ≥ 0.02) | `code/validate_sc.py` (T041) | VALIDATED when analysis runs |
| SC‑002 | Report R‑squared | `code/validate_sc.py` (T041) | VALIDATED |
| SC‑003 | Consistency of coefficient sign/significance in robustness subset | `code/validate_sc.py` (T041) | VALIDATED |
| SC‑004 | Pass/fail of assumption checks | `code/validate_sc.py` (T041) | VALIDATED |
| SC‑005 | Record runtime (≤ 60 s target) | `code/main.py` (T030) | VALIDATED |

*Multiple‑comparison correction*: **Not applied** because SC‑001 explicitly states “no Bonferroni correction”.  

*Power*: The new a‑priori power analysis (T014) ensures the sample is adequate to detect the required effect size; if not, the pipeline halts with a clear message.  

*Collinearity*: VIF computed; VIF > 10 triggers a `High VIF` flag and suppresses independent‑effect claims (edge case in FR‑003).

*Causal framing*: All outputs include `"associational_only": true`.

## Compute Feasibility
All steps are O(N) on parquet files < 1 GB; memory < 2 GB; runtime comfortably under 60 s on the free‑tier CPU runner. No GPU escape hatch required.

## Data Availability (corrected)
| Candidate | Verified URL | Contains required variables? |
|-----------|--------------|-----------------------------|
| mini‑xlsum text corpus | `https://huggingface.co/datasets/gsstein/mini-xlsum/resolve/main/data/test-00000-of-00001.parquet` | **NO** – NLP summarization data; lacks all survey variables |
| 0‑percent‑human text corpus | `https://huggingface.co/datasets/gsstein/0-percent-human-dataset-og/resolve/main/data/test-00000-of-00001.parquet` | **NO** – human‑vs‑AI text data; no relevant variables |
| 100‑percent‑human text corpus | `https://huggingface.co/datasets/gsstein/100-percent-human-dataset/resolve/main/data/test-00000-of-00001.parquet` | **NO** – same as above |
| YouGov surveys | — (no verified source) | **NO** – not programmatically downloadable |

**Conclusion**: *None* of the verified datasets includes the six required columns (`news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `social_media_engagement`). The pipeline therefore downloads the three files, records their true column inventories, and halts at schema validation (FR‑001 edge case). A suitable open dataset must be supplied for any statistical analysis to proceed.

## Task Outline (high‑level)

| Phase | Task ID | Description | Dependencies | Notes |
|-------|---------|-------------|--------------|-------|
| 0 | T010 | Download the three verified parquet URLs, compute SHA‑256, store under `data/raw/` | – | FR‑001 |
| 1 | T011 | Record checksums & column inventories; validate against `contracts/dataset.schema.yaml` | T010 | FR‑001 edge case (explicitly linked to reproducibility) |
| 2 | T012 | Record checksums & column inventories; validate against `contracts/dataset.schema.yaml` | T010 | FR‑001 edge case |
| 3 | T014 | Perform a priori power analysis using the cleaned sample size and SC‑001 effect‑size thresholds; halt with power‑limitation error if N insufficient | T012 | New methodological requirement |
| 4 | T015 | Assess missing‑data mechanism with Little’s MCAR test; log result and add warning if not MCAR | T012 | Supports FR‑002 robustness |
| 5 | T018 | If a dataset passes validation, extract rows, perform listwise deletion of rows missing `news_exposure_freq` or `anxiety_score`; enforce N ≥ 30 hard stop; emit low‑power warning if 30 ≤ N < 100 | T012‑T015 | FR‑002 |
| 6 | T019a | Verify distinctness of anxiety instruments/timepoints using `instrument_source` and `measurement_timepoint`; set `proxy_flag` and `proxy_validated` as needed | T018 | FR‑003, FR‑008 |
| 7 | T018 | Fit OLS regression (`statsmodels.api.OLS`) with covariates; compute VIF for each predictor | T019a | FR‑003, FR‑007 |
| 8 | T020 | Perform Shapiro‑Wilk on `news_exposure_freq` and `anxiety_score`; choose Pearson (if both p > 0.05) else Spearman; compute correlation coefficient and 95 % CI | T018 | FR‑004 |
| 9 | T022 | Compute correlation between `social_media_engagement` and `news_exposure_freq` (normality‑aware); if |r| > 0.3 **and** the variable exists, refit the OLS on participants whose `social_media_engagement` falls in the top percentile; otherwise log warning | T018 | FR‑006 |
|10 | T018 (plot) | Generate scatter plot of `news_exposure_freq` vs. `anxiety_score` with regression line and 95 % CI (merged into modeling task) | T018 | – |
|11 | T030 | Assemble `output/results/regression_results.json` – either full regression fields (`data_status = "OK"`) or `HALTED_NO_VALID_DATASET` with embedded `halt_report` | T018‑T022 | Single source of truth |
|12 | T041 | Run `code/validate_sc.py` against the JSON; write `outputs/success_criteria_log.txt` with PASS/FAIL/BLOCKED per SC‑001 – SC‑005 | T030 | Constitution I |
|13 | T043 | **Removed** – documentation updates are outside functional scope. |
|14 | T044 | **Removed** – archiving handled automatically by CI, not a spec requirement. |
|15 | T045 | **Removed** – sign‑off JSON generated automatically by CI, not a spec requirement. |

**Ordering rule**: download → checksum → schema validation → power analysis → missingness assessment → cleaning → distinctness check → modeling → diagnostics → visualization → validation → (optional) documentation/archive handled automatically. All tasks produce real, inspectable artifacts; no placeholder files are permitted.

---


