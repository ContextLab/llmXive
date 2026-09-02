# Research: Quantifying the Impact of Data Cleaning

## Overview
This document details the research design, data strategy, statistical methods, and validation procedures that will be implemented in the pipeline described in `plan.md`. It follows the functional requirements (FR‑001 – FR‑022) and success criteria (SC‑001 – SC‑012) of the specification.

## Dataset Strategy
Only **open, directly downloadable** datasets are used. The verified URLs provided by the project are:

| Dataset (UCI) | URL | Outcome column (documented) | Size (rows) | Missingness (baseline) |
|---------------|-----|-----------------------------|------------|------------------------|
| Wine Quality | https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv | `quality` (continuous) | 1 599 | [deferred] |
| Breast Cancer Wisconsin Diagnostic | https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/wdbc.data | `diagnosis` (binary) | 569 | [deferred] |
| Heart Disease (Cleveland) | https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data | `target` (binary) | 303 | [deferred] |
| Parkinsons Telemonitoring | | `total_UPDRS` (continuous) | 5 875 | [deferred] |
| Diabetes (Progression) | | `progression` (continuous) | 442 | [deferred] |
| German Credit Data | https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data | `credit_risk` (binary) | 1 000 | [deferred] |
| Adult Income | https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data | `income` (binary) | 32 561 | [deferred] |
| Student Performance | | `G3` (continuous) | 395 | [deferred] |
| Car Evaluation | https://archive.ics.uci.edu/ml/machine-learning-databases/car/car.data | `class_value` (binary) | 1 728 | [deferred] |
| Ionosphere | https://archive.ics.uci.edu/ml/machine-learning-databases/ionosphere/ionosphere.data | `target` (binary) | 351 | [deferred] |
| **Synthetic Benchmark (null effect)** | https://huggingface.co/datasets/MoGP/f_prime_dataset/resolve/main/fpdataset.csv | `target` (continuous) | 1 200 | [deferred] |
| **Synthetic Benchmark (d = 0.5)** | https://huggingface.co/datasets/MoGP/f_prime_dataset/resolve/main/fpdataset.csv | `target` (continuous) | 1 200 | [deferred] |

These twelve datasets satisfy the requirement for at least one dataset per size bin:
- **n < 50**: a 40‑row random sample from *Wine Quality*.
- **50‑200**: a 150‑row random sample from *Heart Disease*.
- **> 200**: the full *Adult Income* (32 561 rows) and other larger sets.

If any bin is empty after sampling, additional open UCI datasets will be fetched from the same verified sources until coverage is achieved (FR‑015).

### Missingness Injection for Sensitivity Analysis
Four missingness levels will be created synthetically:
1. **[deferred]** (original data)
2. **[deferred]** MCAR – random cells set to `NaN`.
3. **[deferred]** MCAR – random cells set to `NaN`.
4. **[deferred]** MAR – missingness introduced conditional on a predictor (high values → missing).

The injection code resides in `code/sensitivity.py` and is deterministic (seeded).

## Statistical Methods
| Analysis | Primary Method | Robust Alternative | Assumption Checks |
|----------|----------------|-------------------|-------------------|
| Two‑sample comparison (binary outcome) | Welch’s t‑test (if variances differ) or standard t‑test (if equal) | Welch’s t‑test always used for safety | Shapiro‑Wilk (α = 0.05), Levene (α = 0.05) |
| Linear regression (continuous outcome) | OLS (`statsmodels.api.OLS`) | Huber‑regression (`statsmodels.robust.robust_linear_model.RLM`) | Shapiro‑Wilk on residuals, Levene on residuals, R² ≥ 0.7 for linearity |
| Effect size | Cohen’s d (pooled SD) for t‑tests; standardized β for regressions | Same (robust) metrics are reported for the alternative models | – |
| Multiple‑comparison correction | Holm‑Bonferroni across all cleaning‑variant p‑values per dataset (FR‑007) | – | – |
| Permutation‑Based FPR | **Outcome permuted *after* cleaning**; outcome column excluded from any cleaning step. 1000 permutations (or 500 for >200 rows) under MCAR & MAR; Holm‑Bonferroni applied per permutation. | – | – |
| Bootstrap variance | Non‑parametric bootstrap, 1000 iterations (`BOOTSTRAP_ITERATIONS`), resampling rows with replacement. | – | – |
| Paired Δ‑metric test | Wilcoxon signed‑rank test on `p_value_delta` across datasets per cleaning operation (FR‑021) | – | – |

All numeric metrics will be stored with at least three decimal places (SC‑002).

## Power Analysis (FR‑016)
A Wilcoxon‑signed‑rank power analysis is performed for each dataset using `statsmodels.stats.power.WilcoxonPower` (medium effect size, α = 0.05, desired power ≥ 0.8). The required sample size per dataset is computed; datasets that do not meet the threshold are flagged in `power_analysis.txt` and treated as a limitation rather than a fatal error. This aligns the power justification with the actual hypothesis test (Wilcoxon) rather than a two‑sample t‑test (SC‑010).

## Validation & Reproducibility
- **Schema Validation**: After each major artifact creation, `code/validation.py` runs `jsonschema.validate` against the contracts in `contracts/`. Failures abort the pipeline (FR‑009, FR‑010, FR‑011, FR‑013, FR‑017, FR‑018).
- **Citation Verification**: The script defined by Principle II (`scripts/verify_citations.py`) cross‑checks every external reference against the source URLs and enforces a title‑overlap ≥ 0.7. Outcome logged in `citation_verification.log`. (FR‑019)
- **Checksum Recording**: SHA‑256 hashes of raw files are stored in `state/projects/PROJ-256-...yaml` as required by Principle III.

## Decision / Rationale (CPU vs GPU)
All statistical methods (t‑tests, regressions, permutation, bootstrap) have efficient CPU implementations in SciPy/Statsmodels. No deep‑learning models are required, so the entire pipeline will run on the GitHub Actions CPU runner. This satisfies the Compute Feasibility clause and avoids the need for a GPU escape hatch.

## Open Issues & Mitigations
- **Dataset Outcome Documentation**: The verified UCI datasets provide clear metadata files; we will parse their README to locate the outcome column. If any ambiguity remains, the dataset will be excluded (FR‑009).
- **Missingness Levels**: The specification left the exact missingness percentages deferred; we have chosen [deferred], [deferred], [deferred], and [deferred] as a transparent, reproducible scheme. This choice is documented in `sensitivity_plan.md`.

---

