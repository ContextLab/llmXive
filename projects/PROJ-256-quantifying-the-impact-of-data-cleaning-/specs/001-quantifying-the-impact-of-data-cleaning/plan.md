# Implementation Plan: Quantifying the Impact of Data Cleaning

**Branch**: `feature/quantify-cleaning-impact` | **Date**: 2026-09-02 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-quantifying-the-impact-of-data-cleaning/spec.md`

## Summary
The project will quantify how common data‑cleaning operations (outlier removal, imputation, categorical recoding) alter statistical inference on a curated set of public datasets. The pipeline will (1) acquire 10‑15 open datasets with a documented binary or continuous outcome, (2) run baseline two‑sample t‑tests and linear regressions, (3) apply cleaning variants (two IQR thresholds, three imputation strategies, two encoding strategies), (4) perform assumption checks and robust fallbacks, (5) estimate permutation‑based false‑positive‑rate (FPR) **after** cleaning while excluding the outcome column from cleaning, (6) adjust p‑values across variants with Holm‑Bonferroni, (7) conduct bootstrap variance estimation, (8) run a factorial sensitivity analysis (cleaning × missingness), (9) perform a Wilcoxon‑based power analysis per dataset, (10) generate a comparison report and visualizations, and (11) validate every artefact against JSON‑Schema contracts.

All steps are orchestrated from `code/main.py` and are fully reproducible on a GitHub Actions CPU runner (2 cores, ≤7 GB RAM). No GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`, `datasets==2.18.*`, `jsonschema==4.22.*`, `matplotlib==3.9.*`, `seaborn==0.13.*`  
- **Storage**: Files under `data/` (raw, processed, intermediate) and JSON artefacts under `data/processed/`.  
- **Testing**: `pytest==8.2.*` with contract‑validation fixtures.  
- **Target Platform**: Linux (GitHub Actions).  
- **Performance Goals**: Entire pipeline ≤ 5 h on the free tier; memory ≤ 6 GB.  
- **Constraints**: All data must be openly downloadable; no external credentials.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | All random seeds are fixed in `code/config.py`; dataset download URLs are hard‑coded; pipeline is a single command (`python -m code.main`). |
| **II. Verified Accuracy** | Every external citation (UCI dataset sources, statistical method references) will be run through the Reference‑Validator before merge. |
| **III. Data Hygiene** | Raw files are stored read‑only; each transformation writes a new file; SHA‑256 checksums are recorded in `state/projects/PROJ-256-...yaml`. |
| **IV. Single Source of Truth** | Every figure/table is generated from the JSON artefacts; the final manuscript pulls values directly from `comparison_report.json`. |
| **V. Versioning Discipline** | All artefacts receive a content hash; the hash map is updated automatically after each run. |
| **VI. Statistical Sensitivity & Variance Estimation** | Bootstrap (≥ 1000) is run for every cleaned variant; sensitivity analysis stratifies by size and missingness; FPR is estimated via permutation **after** cleaning, with outcome excluded from cleaning. |

## Project Structure
```
specs/001-quantifying-the-impact-of-data-cleaning/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── baseline_metrics.schema.yaml
    ├── cleaned_metrics.schema.yaml
    ├── comparison_report.schema.yaml
    ├── analysis_result.schema.yaml
    ├── null_fpr_metrics.schema.yaml
    └── bootstrap_metrics.schema.yaml

code/
├── __init__.py
├── config.py               # seeds, constants, BOOTSTRAP_ITERATIONS
├── data_loader.py          # download & checksum verified datasets
├── analysis.py             # baseline & cleaned statistical tests
├── cleaning.py             # outlier, imputation, recoding, metadata capture
├── assumption_checks.py    # Shapiro‑Wilk, Levene, linearity
├── permutation_fpr.py      # outcome‑permute **after** cleaning, outcome excluded
├── bootstrap.py            # bootstrap CI generation
├── sensitivity.py          # factorial design (cleaning × missingness)
├── reporting.py            # JSON write‑outs, figures, final report
├── validation.py           # schema validation wrapper
└── main.py                 # orchestrates all phases
```

## Phase Overview & FR/SC Mapping
| Phase | Main Tasks | FR(s) addressed | SC(s) addressed |
|-------|------------|-----------------|-----------------|
| **0 – Setup** | Install dependencies, pin seeds, create output directories. | – | – |
| **1 – Dataset Acquisition** | Programmatically download **10–15** open UCI datasets (see Dataset Strategy). Validate each with `contracts/dataset.schema.yaml`. Record outcome column, sample size, missingness in `dataset_metadata.json`. Ensure at least one dataset per size bin (n < 50, 50‑200, >200). If a bin is empty, automatically fetch an additional open dataset. | FR‑001, FR‑009, FR‑017, FR‑015 (bin‑coverage acquisition) | SC‑005, SC‑008 |
| **2 – Baseline Analysis** | For each raw dataset: run two‑sample t‑test / Welch’s test + linear regression, compute p‑value, 95 % CI, effect size (Cohen’s d or standardized β). Store results in `baseline_metrics.json` **and** in `analysis_results.json` (validated against `analysis_result.schema.yaml`). Also compute `ci_overlap` (null for baseline) and `effect_size_change` (null). | FR‑001, FR‑010, FR‑022 | SC‑001, SC‑002 |
| **3 – Cleaning Variants Generation** | For each dataset generate: <br>• Outlier‑removed versions (k = 1.5, 2.0) <br>• Imputed versions (mean, median, KNN) <br>• Recoded versions (one‑hot, label) <br>Metadata (`rows_removed`, `missing_before`, `missing_after`, `variance_reduction`) is returned. | FR‑002, FR‑003, FR‑004, FR‑012, FR‑013, FR‑022 | SC‑001, SC‑002 |
| **4 – Assumption Checks & Robust Fallback** | Before each test, run Shapiro‑Wilk, Levene, linearity (R² ≥ 0.7). If any fail, switch to robust alternatives (Welch’s t‑test or rank‑based regression); flag `assumptions_met: false`. | FR‑006 | SC‑006 |
| **5 – Permutation‑Based FPR** | **(a)** Permute the outcome **after** all cleaning steps (outcome column excluded from cleaning). **(b)** Run the full pipeline on each permuted dataset (default 1000 permutations; 500 for >200 rows). **(c)** Compute proportion of permutations with significant results after Holm‑Bonferroni; store per‑threshold values in `null_fpr_metrics.json`. Also embed the FPR for each variant in `cleaned_metrics.json`. | FR‑006 (FPR estimation) | SC‑006 |
| **6 – Multiple‑Comparison Correction** | Apply Holm‑Bonferroni across all p‑values for a given dataset (all cleaning‑variant p‑values). Store adjusted p‑values in `cleaned_metrics.json`. | FR‑007 | SC‑007 |
| **7 – Bootstrap Variance Estimation** | For each cleaned variant, perform 1000 bootstrap resamples (or `BOOTSTRAP_ITERATIONS`). Store bootstrap CI in `bootstrap_metrics.json`. | FR‑014 | SC‑004 |
| **8 – Sensitivity Analysis** | Conduct a **factorial** sensitivity analysis: for each size bin (n < 50, 50‑200, >200) and each missingness level ([deferred], [deferred], [deferred], [deferred]) run **each cleaning method separately** on both original and missingness‑injected data, capturing interaction effects. Store aggregated results in `sensitivity_metrics.json`. If any bin lacks a dataset, download an additional open dataset that satisfies the criteria. | FR‑008, FR‑015, FR‑022 | SC‑008 |
| **9 – Power Analysis** | Perform a Wilcoxon‑signed‑rank power analysis (medium effect, α = 0.05, power ≥ 0.8) for each dataset using `statsmodels.stats.power.WilcoxonPower`. Document per‑dataset power in `power_analysis.txt`; flag datasets that fall below the threshold. | FR‑016 | SC‑010 |
| **10 – External Benchmark Simulation** | Generate synthetic null‑effect and d = 0.5 datasets (matching size distribution of real data). Run the full pipeline; verify FPR ≤ 0.05 on null data and effect‑size recovery tolerance ±0.1 on non‑null data. | FR‑020 | SC‑012 |
| **11 – Hypothesis‑Testing on Δ‑Metrics** | Compute paired Wilcoxon signed‑rank test on `p_value_delta` across datasets for each cleaning operation; store in `hypothesis_test_results.json`. | FR‑021 | SC‑011 |
| **12 – Report Generation** | Aggregate all delta metrics, CI overlap, effect‑size change, FPR into `comparison_report.json`. Produce forest plot and heatmap under `output/figures/`. | FR‑018 | SC‑003, SC‑009 |
| **13 – Citation Verification** | Run the citation‑validation script required by Principle II; log outcome. | FR‑019 | – |
| **14 – Contract Validation** | After each phase, invoke `code/validation.py` to check JSON artefacts against their schemas (`dataset`, `baseline_metrics`, `cleaned_metrics`, `null_fpr_metrics`, `analysis_results`, etc.). Abort on failure. | FR‑009, FR‑010, FR‑011, FR‑013, FR‑017, FR‑018 | SC‑009 |

## Compute Feasibility
All steps use CPU‑friendly libraries (pandas, scipy, statsmodels, scikit‑learn). The most expensive operation is the permutation‑based FPR (≈ 1000 permutations × 10 datasets × ~5 cleaning variants). Each permutation processes a sampled subset (max 200 rows) to stay within memory/time limits. No GPU is required.

If a future extension demands a transformer‑based model, the plan would off‑load to Kaggle’s free GPU, but the current specification does **not** need it.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Insufficient open datasets matching size/missingness bins. | Use the verified UCI datasets listed in the “Dataset Strategy” table; they are programmatically downloadable and can be filtered to meet bin criteria. |
| Permutation FPR computation exceeds runtime. | Limit permutations to 500 for datasets with > 200 rows; note the power limitation in `sensitivity_metrics.json`. |
| Schema drift (e.g., new fields added). | All schema files are version‑controlled; validation step will catch mismatches before downstream use. |

---

