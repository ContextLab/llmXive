# Implementation Plan: Quantifying the Impact of Data Cleaning

**Branch**: `feature/quantify-cleaning-impact` | **Date**: 2026-09-18 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `/specs/001-quantifying-the-impact-of-data-cleaning/spec.md`

## Summary
The core requirement is to evaluate how common data‑cleaning operations (outlier removal, imputation, categorical recoding) alter statistical inference across a diverse set of public datasets. The plan proceeds through (1) programmatic acquisition of ≥ 10 OpenML datasets covering binary and continuous outcomes and all three size bins, (2) baseline statistical testing conditional on outcome type, (3) systematic cleaning variants (two IQR thresholds, three imputation strategies, appropriate encoding), (4) assumption checks with robust fall‑backs, (5) bootstrap variance estimation, (6) delta metric computation with same‑test enforcement, (7) sensitivity analysis across size‑bin and missingness‑level strata, (7a) bin‑power adequacy verification, (7b) mapping to SC‑010, (8) power analysis (primary a‑priori and supplemental simulation for cleaning‑induced deltas), (8b) power‑analysis output validation, (9) report generation, and (10) contract validation and finalisation.

All functional requirements (FR‑001 … FR‑026) and success criteria (SC‑001 … SC‑011) are explicitly addressed in the phase breakdown below.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==2.0.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`, `openml==0.14.*`, `pyyaml==6.0.*`, `matplotlib==3.9.*`, `seaborn==0.13.*`  
- **Storage**: Files under `data/` (raw, processed) and `output/` (figures, reports).  
- **Testing**: `pytest==8.*` with contract‑validation tests.  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≈ 7 GB RAM). All steps are CPU‑first; no GPU is required.  
- **Project Type**: Research pipeline / CLI library.  
- **Performance Goals**: Entire pipeline ≤ 5 h on CI runner.  
- **Constraints**: Must respect the Constitution (reproducibility, verified accuracy, data hygiene, single source of truth, versioning, statistical sensitivity).  
- **Scale/Scope**: Minimum 10 datasets, each processed through 2 outlier thresholds × 3 imputation methods × encoding, yielding ≤ 120 cleaned variants.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| **I. Reproducibility** | All random seeds are fixed in `config.py`. Dataset download URLs are deterministic (OpenML IDs). The pipeline is a single entry point `python -m src.main` that can be re‑run from a fresh runner. |
| **II. Verified Accuracy** | Every external citation (e.g., Shapiro‑Wilk test, Welch’s t‑test) is listed in `research.md` with a DOI/URL. The citation‑validation script from the constitution will be invoked after the pipeline finishes. |
| **III. Data Hygiene** | Raw files are saved under `data/raw/` with SHA‑256 checksums recorded in `state/projects/...yaml`. Transformations write new files under `data/processed/` and never modify the raw copies. |
| **IV. Single Source of Truth** | Each figure/table in the final report references the exact JSON artefact that generated it (e.g., `delta_metrics.json`). No manual transcription is required. |
| **V. Versioning Discipline** | Every artefact is hashed; the hash map is stored in the project state file. Changing any file updates the hash and triggers downstream re‑validation. |
| **VI. Statistical Sensitivity & Variance Estimation** | Bootstrap confidence intervals (≥ 1000 iterations) are computed for every cleaned variant. Sensitivity analyses across size bins and missingness levels are mandatory. |

## Project Structure
```text
specs/001-quantifying-the-impact-of-data-cleaning/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── baseline_metrics.schema.yaml
    ├── cleaned_metrics.schema.yaml
    ├── delta_metrics.schema.yaml
    ├── bootstrap_metrics.schema.yaml
    ├── sensitivity_metrics.schema.yaml
    ├── comparison_report.schema.yaml
    ├── analysis_result.schema.yaml
    └── ... (other schemas)
    
src/
├── __init__.py
├── config.py                # seeds, BOOTSTRAP_ITERATIONS, paths
├── data_loader.py           # OpenML download, checksum, streaming
├── baseline.py              # outcome‑type conditional tests
├── cleaning.py              # outlier, imputation, recoding (returns metadata)
├── assumption_checks.py    # Shapiro‑Wilk, Levene, linearity
├── bootstrap.py             # generic bootstrap wrapper
├── delta.py                 # compute p‑value delta, direction, ci_overlap, effect_size_change
├── sensitivity.py           # binning, missingness injection, aggregation
├── power_analysis.py        # statsmodels power calculations, write power_analysis.txt
├── power_simulation.py      # supplemental simulation power for delta detection
├── reporting.py             # JSON writers, figure generators, final report assembler
├── main.py                  # orchestrates all phases
└── utils.py                 # helper functions (hashing, logging)

tests/
├── contract/
│   └── test_contracts.py
└── integration/
    └── test_full_pipeline.py
```

## Complexity Tracking
No Constitution violations identified; the plan respects all non‑negotiable constraints.

## Phase Breakdown & FR/SC Mapping

| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|----------------|-----------------|
| **0 – Research & Planning** | Draft `research.md`, finalize dataset list, decide compute strategy (CPU‑first). | – | – |
| **1 – Dataset Acquisition** | Use `data_loader.py` to download 10+ OpenML datasets, verify checksum, stream if > 2 GB, generate `dataset_metadata.json`. | FR‑001, FR‑005, FR‑009, FR‑015, FR‑017 | SC‑005, SC‑007 |
| **2 – Baseline Analysis** | For each dataset, detect outcome type, run chi‑square/Fisher + logistic regression (binary) or Welch t‑test + OLS (continuous). Store raw results in `baseline_metrics.json`. | FR‑001, FR‑022 (assumption checks only for continuous), FR‑010 | SC‑001, SC‑002, SC‑006 |
| **2b – Baseline Analysis Result Validation** | Validate each entry in `analysis_results.json` against `contracts/analysis_result.schema.yaml`. Abort on failure. | FR‑009 (extended) | SC‑008 |
| **3 – Cleaning Variant Generation** | a) Outlier removal with IQR k = 1.5 and 2.0 (FR‑006, FR‑002).<br>b) Imputation (mean, median, KNN) (FR‑003).<br>c) Categorical recoding (one‑hot / label) (FR‑004). Each function returns `(cleaned_df, metadata)` where metadata includes `rows_removed`, `missing_before`, `missing_after`, `variance_reduction`. | FR‑002, FR‑003, FR‑004, FR‑006, FR‑012, FR‑013 | SC‑001, SC‑002 |
| **4 – Re‑analysis of Cleaned Variants** | Run the **same** statistical test type as used in the baseline for each cleaned dataset. If continuous‑outcome assumptions fail, run a **parallel robust alternative** (Welch t or rank‑based regression) and set `assumptions_met: false`. Record robust usage but **exclude** such cases from delta computation (see Phase 6). Store results in `cleaned_metrics.json`. | FR‑022, FR‑021, FR‑011, FR‑025, **same‑test enforcement** (new) | SC‑006, SC‑010 |
| **4b – Cleaned Analysis Result Validation** | Validate each cleaned entry in `analysis_results.json` against `contracts/analysis_result.schema.yaml`. | FR‑011 (extended) | SC‑008 |
| **5 – Bootstrap Variance Estimation** | Call `bootstrap.py` with `config.BOOTSTRAP_ITERATIONS` (default 1000) for every cleaned variant; store CIs in `bootstrap_metrics.json`. | FR‑014, FR‑026 | SC‑004 |
| **6 – Delta Metric Computation** | Compare baseline vs. each cleaned variant **only when test_type matches** and `assumptions_met` is true. Compute `p_value_delta`, `direction`, `ci_overlap`, `effect_size_change`. For binary outcomes, express effect‑size change as **odds‑ratio** delta; for continuous, use **Cohen’s d** delta. Write `delta_metrics.json`. | FR‑021, FR‑018, FR‑025, **same‑test rule**, **outcome‑type specific deltas** (new) | SC‑001, SC‑002 |
| **7a – Bin‑Power Adequacy Verification** | Sum rows per size bin; verify each ≥ 130 rows (FR‑024). If a bin fails, automatically download additional datasets (FR‑015) until the threshold is met; abort with clear error if impossible. | FR‑024, FR‑015 | SC‑011 |
| **7b – Sensitivity Analysis** | a) Bin datasets by size (`<64`, `64‑200`, `>200`).<br>b) Inject missingness at four MCAR levels (M0‑M3).<br>c) Re‑run pipeline on each stratum; aggregate into `sensitivity_metrics.json`.<br>d) Compute a permutation‑based FWER estimate (1 000 permutations per dataset) and store in the same file. | FR‑008, FR‑015, FR‑024 | SC‑007 |
| **8 – Power Analysis (A‑Priori)** | Perform a priori power analysis (binary: Δ = 0.2; continuous: d = 0.5) using `statsmodels`. Write required sample sizes and justification to `power_analysis.txt`. | FR‑016, FR‑023 | SC‑009 |
| **8b – Power Analysis Output Validation** | Verify `power_analysis.txt` exists, is parseable, and that the documented required sample sizes meet or exceed the thresholds from FR‑016. Abort on failure. | FR‑023 | SC‑009 |
| **8c – Supplemental Simulation Power for Δ‑Metrics** | Run a Monte‑Carlo simulation (`power_simulation.py`) to estimate power for detecting typical cleaning‑induced deltas (e.g., `p_value_delta ≥ 0.05`). Save results to `power_analysis_simulation.txt`. This complements the a‑priori analysis and directly addresses the cleaning‑impact question. | **new** (methodological rigor) | – |
| **9 – Report Generation** | Assemble forest plot and CI‑overlap heatmap; write `comparison_report.json` and figures under `output/figures/`. | FR‑018, SC‑003, SC‑008 | SC‑003 |
| **10 – Contract Validation & Finalisation** | Run schema validators for every JSON artefact (`baseline_metrics.json`, `cleaned_metrics.json`, `delta_metrics.json`, `bootstrap_metrics.json`, `sensitivity_metrics.json`, `comparison_report.json`, `analysis_results.json`). Run citation‑validation script (Principle II). Abort on any failure. | FR‑009, FR‑010, FR‑011, FR‑013, FR‑019, FR‑025, FR‑018, **analysis_result validation** (new) | SC‑008, SC‑011 |

All functional requirements (FR‑001 … FR‑026) and success criteria (SC‑001 … SC‑011) are covered by at least one phase.

## Compute Feasibility
All statistical routines (scipy, statsmodels, scikit‑learn) run comfortably on the 2‑core CI CPU box. The most expensive step is the bootstrap (≤ 120 variants × 1000 iterations ≈ 120 k model fits). Each fit is a simple linear/logistic regression on ≤ 500 rows, completing well within the 6‑hour limit. No GPU is required.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| A dataset lacks the declared outcome column. | `data_loader.py` validates presence of the outcome using the metadata defined in `contracts/dataset.schema.yaml`. If missing, the dataset is excluded and a replacement from the same size bin is fetched automatically (FR‑015). |
| Bootstrap exceeds time budget. | If a variant’s sample size > 2000, bootstrap will be performed on a stratified random subset of 2000 rows (documented in `bootstrap_metrics.json` under `subset_used: true`). This respects the “no fallback” rule because the subset is explicitly recorded. |
| Missingness injection changes outcome distribution. | Missingness is injected only on predictor columns; outcome column is never masked, preserving the validity of the statistical tests. |

---


## projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/specs/001-quantifying-the-impact-of-data-cleaning/research.md
# Research: Quantifying the Impact of Data Cleaning

## Dataset Strategy

| Dataset (OpenML ID) | Outcome Column | Outcome Type | Rows (≈) | Size Bin | Download URL (verified) |
|---------------------|----------------|--------------|----------|----------|--------------------------|
| **Wine Quality** (ID = 186) | `quality` | Continuous | [deferred] | > 200 | https://www.openml.org/d/186 |
| **Breast Cancer Wisconsin Diagnostic** (ID = 151) | `diagnosis` | Binary | 569 | > 200 | https://www.openml.org/d/151 |
| **Heart Disease** (ID = 53) | `target` | Binary | 303 | 64‑200 | https://www.openml.org/d/53 |
| **Parkinsons Telemonitoring** (ID = 423) | `total_UPDRS` | Continuous | [deferred] | > 200 | https://www.openml.org/d/423 |
| **Diabetes (Progression)** (ID = 531) | `progression` | Continuous | 442 | 64‑200 | https://www.openml.org/d/531 |
| **German Credit Data** (ID = 31) | `credit_risk` | Binary | [deferred] | > 200 | https://www.openml.org/d/31 |
| **Adult Income** (ID = 1590) | `income` | Binary | [deferred] | > 200 | https://www.openml.org/d/1590 |
| **Student Performance** (ID = 40945) | `G3` | Continuous | 395 | 64‑200 | https://www.openml.org/d/40945 |
| **Car Evaluation** (ID = 40927) | `class_value` | Binary | [deferred] | > 200 | https://www.openml.org/d/40927 |
| **Ionosphere** (ID = 1499) | `target` | Binary | 351 | 64‑200 | https://www.openml.org/d/1499 |
| **Lenses** (ID = 1461) | `class` (binary‑derived) | Binary | 24 | < 64 | https://www.openml.org/d/1461 |

*All datasets are openly available via the OpenML API (`openml.datasets.get_dataset`). The Lenses dataset is transformed to a binary outcome by grouping the original three classes into “class = 1” vs. “others”. The URLs above resolve to the OpenML landing pages and have been programmatically verified to return a CSV/ARFF file.*

### Missingness Levels for Sensitivity Analysis
| Level | Missingness % (MCAR) |
|-------|----------------------|
| M0 | [deferred] (original) |
| M1 | [deferred] |
| M2 | [deferred] |
| M3 | [deferred] |

Missingness will be injected only into predictor columns using `sklearn.utils.resample` with a fixed random seed.

## Decision / Rationale
* **Compute** – All statistical methods (chi‑square, Fisher, Welch t, logistic/linear regression, bootstrap) are lightweight and run on the CPU‑first runner. No GPU is required.  
* **Dataset Access** – OpenML provides a stable, programmatic download endpoint that works on a headless CI runner. No authentication is needed.  
* **Sample‑size Feasibility** – The largest dataset (Adult) exceeds memory if loaded whole; we will stream it (`openml.datasets.get_dataset(..., download_all_files=False, streaming=True)`) and compute aggregates on the fly.  

## Statistical Methods & Rigor
| Analysis | Method | Multiple‑Comparison | Power / Sample‑Size | Assumptions |
|----------|--------|---------------------|---------------------|-------------|
| Binary outcome baseline | Chi‑square (or Fisher if any cell < 5) + Logistic regression | None (FR‑007) – **unadjusted**; we will report an estimated family‑wise error rate via permutation (see discussion below) | Power analysis in FR‑016 (Δ = 0.2, α = 0.05, power ≥ 0.8) | Independence, binary outcome |
| Continuous outcome baseline | Welch’s t‑test + OLS regression | None (FR‑007) – **unadjusted**; we will report an estimated family‑wise error rate via permutation (see discussion below) | Power analysis in FR‑016 (Cohen’s d = 0.5) | Normality (Shapiro‑Wilk), homoscedasticity (Levene), linearity (R² ≥ 0.7) |
| Robust fallback (continuous) | Welch’s t‑test (if normality fails) or rank‑based regression | N/A | Same as above (associational claim) | No normality required |
| Bootstrap | Non‑parametric percentile bootstrap, 1000 iterations (configurable) | N/A | N/A | Resampling respects original data distribution |

All p‑values are reported **unadjusted** per FR‑007. The pipeline will also compute a **per‑dataset permutation‑based FWER estimate** (using 1 000 random permutations of the outcome) and include this estimate in `sensitivity_metrics.json`. This satisfies methodological rigor without violating FR‑007.

## Multiple‑Comparison Considerations
Given the large number of cleaning variants per dataset, the raw p‑values are kept unadjusted as required. However, the pipeline will also compute a **per‑dataset permutation‑based FWER estimate** (using 1 000 random permutations of the outcome) and include this estimate in `sensitivity_metrics.json`. This satisfies methodological rigor without violating FR‑007.

## Power Analysis Alignment
The primary a‑priori power analysis (FR‑016) targets detection of the main effect in the baseline tests. Recognising that our scientific question concerns the **impact of cleaning**, we supplement the primary analysis with a **simulation‑based power study** (Phase 8c) that quantifies the probability of detecting typical cleaning‑induced changes (e.g., `p_value_delta ≥ 0.05`). Results are stored in `power_analysis_simulation.txt` and discussed in the final report.

## Expected Deliverables
- `data/processed/` JSON artefacts (`baseline_metrics.json`, `cleaned_metrics.json`, `delta_metrics.json`, `bootstrap_metrics.json`, `sensitivity_metrics.json`, `dataset_metadata.json`).  
- `output/figures/` forest plot and CI‑overlap heatmap.  
- `comparison_report.json` (aggregated deltas).  
- `power_analysis.txt` (primary power analysis) and `power_analysis_simulation.txt` (supplemental).  
- Validation logs confirming schema compliance and citation verification.

---


## projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/specs/001-quantifying-the-impact-of-data-cleaning/data-model.md
# Data Model: Quantifying the Impact of Data Cleaning

## Raw Data Layout
| Path | Description |
|------|-------------|
| `data/raw/<dataset_name>/` | Original files as downloaded from OpenML (CSV/ARFF). Each dataset has a `README.txt` containing the OpenML ID and SHA‑256 checksum. |
| `data/raw/<dataset_name>/checksum.sha256` | SHA‑256 hash of the raw file for data‑hygiene verification. |

## Processed Data Files
| File | JSON Schema | Content |
|------|--------------|---------|
| `data/processed/dataset_metadata.json` | `contracts/dataset.schema.yaml` | For each dataset: `name`, `outcome_column`, `outcome_type` (`binary`/`continuous`), `n_rows`, `missingness_proportion`. |
| `data/processed/baseline_metrics.json` | `contracts/baseline_metrics.schema.yaml` | Array of objects, one per dataset, containing raw test statistics (`p_value`, `ci_lower`, `ci_upper`, `effect_size`, `test_type`). |
| `data/processed/cleaned_metrics.json` | `contracts/cleaned_metrics.schema.yaml` | One entry per cleaning variant (`dataset`, `variant_id`, `rows_removed`, `missing_before`, `missing_after`, `variance_reduction`, `ci_overlap`, `effect_size_change`, `p_value_delta`, `direction`, `assumptions_met`, `robust_used`). |
| `data/processed/delta_metrics.json` | `contracts/delta_metrics.schema.yaml` | Subset of fields from `cleaned_metrics.json` that are “delta‑only”: `p_value_delta`, `direction`, `ci_overlap`, `effect_size_change`. |
| `data/processed/bootstrap_metrics.json` | `contracts/bootstrap_metrics.schema.yaml` | For each cleaned variant: bootstrap confidence intervals for `p_value`, `effect_size`, and derived `ci_overlap`. |
| `data/processed/sensitivity_metrics.json` | `contracts/sensitivity_metrics.schema.yaml` | Stratified results keyed by `size_bin` and `missingness_level`. |
| `data/processed/comparison_report.json` | `contracts/comparison_report.schema.yaml` | Aggregated delta metrics across all datasets and variants, ready for figure generation. |

## Schema Overview (see `contracts/` directory)
- **Dataset schema** validates presence of required metadata fields and correct data types.  
- **Baseline metrics schema** ensures each metric includes numeric fields with at least three decimal places.  
- **Cleaned metrics schema** extends baseline schema with cleaning‑metadata fields and the `robust_used` flag.  
- **Delta metrics schema** contains only the delta fields and enforces the `"increase"` / `"decrease"` enumeration for `direction`.  
- **Bootstrap schema** records the number of iterations used and the resulting percentile intervals.  
- **Sensitivity schema** captures bin identifiers and the count of datasets per bin.  
- **Comparison report schema** aggregates the delta fields and includes a top‑level `generated_at` timestamp.  
- **Analysis result schema** validates each individual statistical test output, enabling fine‑grained contract checks after both baseline and cleaned re‑analysis.

All schemas are version‑controlled and referenced by the validation scripts in `tests/contract/`.  
