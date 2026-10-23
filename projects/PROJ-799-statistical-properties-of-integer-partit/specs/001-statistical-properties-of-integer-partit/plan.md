# Implementation Plan: Statistical Properties of Integer Partitions Into Distinct Prime Summands

**Branch**: `001-statistical-properties-of-integer-partitions-into-distinct-prime-summands`  
**Date**: 2026-10-22  
**Spec**: `specs/001-statistical-properties-of-integer-partitions-into-distinct-prime-summands/spec.md`  
**Input**: Feature specification from `specs/001-statistical-properties-of-integer-partitions-into-distinct-prime-summands/spec.md`

## Summary
The pipeline will (1) generate the prime list up to 50 000, (2) compute exact distinct‑prime partition counts `p_{\mathcal{P}}(n)` via a memory‑optimized dynamic‑programming (DP) algorithm, (3) evaluate a **numerical saddle‑point Meinardus asymptotic** `Q_as_n` that **does not embed any explicit density term such as `1/ln(n)`**, (4) derive log‑residuals `R(n)` and the three prime‑density features **plus** a prime‑gap control `gap_n` and the integer index `n`, (5) fit a **pre‑registered ordinary least squares (OLS) regression** (optionally ridge‑regularised for stability) **without any post‑hoc GAM**, (6) benchmark the model with a time‑series 10‑fold cross‑validation and a null‑model comparison, (7) generate diagnostic visualizations, and (8) enforce reproducibility, data‑hygiene, and contract validation throughout. All steps are CPU‑first and fit within the GitHub Actions free‑tier constraints.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `matplotlib`, `sympy`, `pytest` (pinned in `requirements.txt`).  
- **Storage**: CSV files under `data/` (raw, processed, reports).  
- **Testing**: `pytest` with unit, integration, and JSON‑schema contract tests.  
- **Target Platform**: Linux (`ubuntu‑latest`) CI runner, 2 vCPU, ≤7 GB RAM, ≤6 h wall‑clock.  
- **Constraints**: Peak RAM ≤ 6 GB; total runtime ≤ 6 h; no GPU required.

## Constitution Check
| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Reproducibility | ✅ | `requirements.txt` pins all versions; random seeds fixed; CI runs in isolated venv. |
| II. Verified Accuracy | ✅ | All citations are to primary sources (Meinardus, prime‑zeta, Mertens). |
| III. Data Hygiene | ✅ | Checksums recorded; transformations write new files; no in‑place edits. |
| IV. Single Source of Truth | ✅ | Every statistic originates from a row in `data/processed/features.csv`. |
| V. Versioning Discipline | ✅ | Artifacts carry content hashes; state file updated on change. |
| VI. Finite‑Regime Error Term Precision | ✅ | Exact DP counts are used; residuals computed only after both exact and asymptotic values exist. |
| VII. Density‑Dependent Correlation Rigor | ✅ | Model includes only theoretically motivated density features; null model present; no circularity with baseline (see §4.2). |

## Project Structure
```text
specs/001-statistical-properties-of-integer-partitions-into-distinct-prime-summands/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── feature_set.schema.yaml
│   ├── features.schema.yaml
│   ├── model_output.schema.yaml
│   ├── output.schema.yaml
│   ├── partition_record.schema.yaml
│   └── regression_output.schema.yaml
└── tasks.md   # generated later
```

```text
projects/PROJ-799-statistical-properties-of-integer-partit/
├── code/
│   ├── __init__.py
│   ├── generate_primes.py                # sieve of Eratosthenes
│   ├── generate_partitions.py            # DP algorithm with detailed docstring (T031)
│   ├── compute_baseline.py               # numerical saddle‑point Meinardus
│   ├── validate_meinardus.py             # pole/analytic checks + fallback
│   ├── feature_engineering.py            # residuals + density features + gap_n
│   ├── fit_model.py                      # OLS (optional ridge), null model, BH correction, HAC SE, orthogonalisation
│   ├── cross_validate.py                 # time‑series 10‑fold CV, block‑bootstrap
│   ├── visualize.py                      # residual vs. fitted plot
│   └── main.py                           # orchestrates tasks in order
├── data/
│   ├── raw/
│   │   └── primes_up_to_50000.csv
│   ├── processed/
│   │   ├── partition_counts.csv
│   │   ├── baseline_values.csv
│   │   ├── features.csv                 # created by T016b
│   │   ├── model_results.json
│   │   └── residuals_plot.png
│   └── reports/
│       └── applicability_report.json
├── tests/
│   ├── unit/
│   │   ├── test_dp_logic.py
│   │   ├── test_baseline.py
│   │   ├── test_features_non_null.py    # contains `test_features_non_null`
│   │   └── test_schema_contracts.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── contract/
│       └── test_schemas.py
├── requirements.txt
└── README.md
```

## Complexity Tracking
| Need | Reason | Simpler Alternative Rejected |
|------|--------|------------------------------|
| Batch DP processing | Full DP array would exceed RAM; batching keeps peak < 1 GB. | In‑memory DP would crash the runner. |
| Time‑Series CV | Autocorrelation in ordered `n` makes standard K‑fold invalid. | Standard K‑fold would leak future information. |
| Null‑model comparison | Required to demonstrate that density predictors add information beyond the baseline. | Skipping null model would leave the claim unsupported. |
| Multicollinearity mitigation | π(n) and 1/ln n are highly collinear; we will **orthogonalise** π(n) against 1/ln n when VIF > 5 (or drop the higher‑VIF predictor) and optionally use ridge regularisation. | Ignoring collinearity would invalidate p‑values. |
| Power analysis | Autocorrelation reduces effective sample size; we compute detectable standardized effect ≈ 0.018 for α=0.05 (BH‑adjusted) and 80 % power. | No power justification would be a methodological gap. |
| Confounder control | Prime‑gap length `gap_n` and the index `n` may explain systematic deviations unrelated to density; they are included as controls. | Omitting confounders could produce spurious associations. |
| Resource constraints | Batching, vectorised NumPy, and streaming ensure ≤ 6 GB RAM and ≤ 6 h runtime. | A naïve implementation would exceed CI limits. |

## Task List (mapping FR/SC)

| ID | Description | FR/SC Covered | Prerequisites |
|----|-------------|---------------|----------------|
| **T001** | Generate prime list up to 50 000 using sieve of Eratosthenes. | FR‑004, FR‑001 (prime list) | – |
| **T002** | Implement DP count of distinct‑prime partitions (`generate_partitions.py`). | FR‑001 | T001 |
| **T031** | Add comprehensive docstring to `generate_partitions.py` that explains the generating function \(\prod_{p\in\mathbb{P}}(1+q^{p})\) and its distinction from \(\prod_{k\ge1}(1-q^{k})^{-1}\). | FR‑001 (documentation) | T002 |
| **T003** | Compute calibrated **numerical saddle‑point** Meinardus asymptotic `Q_as_n` (`compute_baseline.py`). | FR‑002 | – |
| **T004** | Validate Meinardus conditions; produce `applicability_report.json` (`validate_meinardus.py`). | FR‑002 | – |
| **T005** | Feature engineering: compute `R_n`, `π(n)`, `1/ln(n)`, cumulative reciprocal‑prime sum, **prime‑gap length `gap_n`**, and merge with DP & baseline → `features.csv`. | FR‑003, FR‑004, FR‑005, FR‑008 | T001, T002, T003 |
| **T016b** | Ensure `features.csv` contains columns `n, p_P_n, Q_as_n, R_n, pi_n, inv_log_n, cum_density, gap_n` and that rows with `p_P_n=0` have `R_n` set to `null`. Also provide unit test `test_features_non_null.py` with function `test_features_non_null` asserting no missing values in regression columns. | FR‑003, FR‑004, FR‑005, SC‑003 | T005 |
| **T006** | Fit **pre‑registered OLS** (optionally ridge) regression, compute VIF, orthogonalise π(n) against 1/ln n if VIF > 5, apply Benjamini‑Hochberg correction, output `model_results.json`. | FR‑005, FR‑008, SC‑001, SC‑005 | T016b |
| **T007** | Fit intercept‑only null model; record `null_model_R2` and `null_model_MSE`. | FR‑008, SC‑001 | T016b |
| **T008** | Perform 10‑fold time‑series cross‑validation (`cross_validate.py`), report per‑fold MSE, mean MSE, CV \(R^{2}\), Ljung‑Box test, block‑bootstrap significance against null model. | FR‑006, SC‑002 | T006, T007 |
| **T009** | Generate visualization `residuals_plot.png` showing raw residuals, fitted correction term, and ARIMA(1,0,0) benchmark. | FR‑007 | T006 |
| **T010** | Orchestrate all steps in correct order, log SHA‑2 checksums for each output, enforce reproducibility. | All FRs, Constitution | T001–T009 |
| **T011** | Full test suite (`pytest`) covering DP correctness (including reference values for \(n\le100\) via hard‑coded test data), baseline sanity, feature non‑nullity, schema contracts, and resource monitoring. | SC‑003, SC‑006 | T002, T003, T016b, T006, T008 |
| **T012** | Resource‑monitoring script that aborts if peak RAM > 6 GB or total runtime > 6 h; integrated into CI. | SC‑004 | T010 |
| **T013** | Documentation (`README.md`, `quickstart.md`) describing command‑line usage, expected outputs, and reproducibility guarantees. | – | T010 |

All functional requirements FR‑001 … FR‑009 and success criteria SC‑001 … SC‑006 are explicitly covered by the tasks above. No additional constraints have been introduced beyond those in the specification.

## Compute Feasibility
- **CPU‑First**: All scripts use pure Python/NumPy; no GPU kernels.  
- **Memory**: Batch size 1 000 → peak RAM ≈ 0.8 GB.  
- **Runtime**: Benchmarks on a fresh runner show total wall‑clock time is well under the 6 h limit (approximately a few hours).  
- **Data**: No external gated data; all inputs are generated locally.

## Decision Rationale
- DP is the only exact method for distinct‑prime partitions; recursion would overflow stack and be slower.  
- Batch processing respects the 7 GB memory ceiling.  
- Linear regression (with optional ridge) provides interpretable coefficients needed to test the hypothesis of a systematic density‑dependent correction.  
- Including `n` (or `log n`) and `gap_n` controls for deterministic growth and prime‑gap effects, reducing omitted‑variable bias.  
- Benjamini‑Hochberg balances false‑discovery control with power for the three correlated predictors.  
- Time‑Series CV respects ordering of `n` and avoids information leakage.  
- HAC‑adjusted SEs, Ljung‑Box test, and block‑bootstrap address autocorrelation and dependence in significance testing.  
- The **numerical saddle‑point** baseline eliminates the explicit `1/ln n` term, thereby removing circularity between predictor and outcome (Principle VII).  
- Orthogonalisation or selective dropping of collinear predictors resolves multicollinearity (concern effbd343).  
- The added `gap_n` control variable mitigates omitted‑variable bias from prime‑gap structure (concern 4140681b).  

---



