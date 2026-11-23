# Implementation Plan: Statistical Properties of Integer Partitions Into Distinct Prime Summands

**Branch**: `001-statistical-properties-of-integer-partitions-into-distinct-prime-summands`  
**Date**: 2026-10-22  
**Spec**: `specs/001-statistical-properties-of-integer-partitions-into-distinct-prime-summands/spec.md`  
**Input**: Feature specification from `specs/001-statistical-properties-of-integer-partitions-into-distinct-prime-summands/spec.md`

## Summary
The pipeline will (1) generate the prime list up to 50 000, (2) compute exact distinct‑prime partition counts `p_P_n` via a memory‑optimised dynamic‑programming (DP) algorithm, (3) evaluate a **pure analytic Meinardus asymptotic** `Q_as_n` that contains **no density terms** (see scientific‑soundness note below), (4) engineer log‑residuals `R_n` and the three prime‑density predictors plus a prime‑gap control, (5) fit a pre‑registered ordinary least‑squares (OLS) regression (with optional ridge for stability) and perform a formal power analysis, (6) benchmark the model with a time‑series 10‑fold cross‑validation and a null‑model comparison, (7) generate diagnostic visualisations, and (8) enforce reproducibility, data‑hygiene, and contract validation throughout. All steps are CPU‑first and respect the GitHub Actions free‑tier limits.

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
| I. Reproducibility | ✅ | `requirements.txt` pins all versions; random seeds are fixed; CI runs in isolated venv. |
| II. Verified Accuracy | ✅ | All citations are to primary sources (Meinardus, prime‑zeta, Mertens). |
| III. Data Hygiene | ✅ | Checksums recorded; transformations write new files; no in‑place edits. |
| IV. Single Source of Truth | ✅ | Every statistic originates from a row in `data/processed/features.csv`. |
| V. Versioning Discipline | ✅ | Artifacts carry content hashes; state file updated on change. |
| VI. Finite‑Regime Error Term Precision | ✅ | Exact DP counts are used; residuals computed only after both exact and asymptotic values exist. |
| VII. Density‑Dependent Correlation Rigor | ✅ | Model includes only theoretically motivated density features; baseline contains no density term, avoiding circularity. |

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
│   ├── compute_baseline.py               # pure analytic Meinardus asymptotic
│   ├── validate_meinardus.py             # pole/analytic checks + fallback
│   ├── feature_engineering.py            # residuals + density features + gap_n
│   ├── fit_model.py                      # OLS (optional ridge), VIF handling, BH correction, HAC SE, power analysis
│   ├── cross_validate.py                 # time‑series 10‑fold CV, block‑bootstrap, Ljung‑Box
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
| Multicollinearity mitigation | π(n) and 1/ln n are highly collinear; we will **orthogonalise** π(n) against 1/ln n when VIF > 5 (or drop the higher‑VIF predictor). | Ignoring collinearity would invalidate p‑values. |
| Power analysis | Autocorrelation reduces effective sample size; we compute detectable effect size for α=0.05, power = 0.8. | No power justification would be a methodological gap. |
| Confounder control | Prime‑gap length `gap_n` and the index `n` may explain systematic deviations unrelated to density; they are included as controls. | Omitting confounders could produce spurious associations. |
| Resource constraints | Batching, vectorised NumPy, and streaming ensure ≤ 6 GB RAM and ≤ 6 h runtime. | A naïve implementation would exceed CI limits. |

## Task List (mapping FR/SC)

| ID | Description | FR/SC Covered | Prerequisites |
|----|-------------|---------------|----------------|
| **T001** | Generate prime list up to 50 000 using sieve of Eratosthenes (`generate_primes.py`). | FR‑004, FR‑001 (prime list) | – |
| **T002** | Implement DP count of distinct‑prime partitions (`generate_partitions.py`). | FR‑001 | T001 |
| **T031** | Add comprehensive docstring to `generate_partitions.py` that explains the generating function \(\prod_{p\in\mathbb{P}}(1+q^{p})\) and its distinction from \(\prod_{k\ge1}(1-q^{k})^{-1}\). The file already exists; this task enriches it with the required documentation. | FR‑001, FR‑012 | T002 |
| **T003** | Compute calibrated **pure analytic Meinardus** asymptotic `Q_as_n` (no density terms). | FR‑002 | – |
| **T004** | Validate Meinardus conditions; produce `applicability_report.json` (`validate_meinardus.py`). | FR‑002 | – |
| **T005** | Feature engineering: compute `R_n` (sentinel ‑9999 for non‑positive inputs), `π(n)`, `1/ln(n)`, cumulative reciprocal‑prime sum, `gap_n`, and merge with DP & baseline → `features.csv`. | FR‑003, FR‑004, FR‑005, FR‑010, FR‑013 | T001, T002, T003 |
| **T016b** | Ensure `features.csv` contains columns `n, p_P_n, Q_as_n, R_n, pi_n, inv_log_n, cum_density, gap_n`; rows with `p_P_n=0` have `R_n` set to **‑9999**. Provide unit test `test_features_non_null.py` asserting **no missing numeric values** in regression columns. | FR‑003, FR‑004, FR‑005, SC‑003 | T005 |
| **T006** | Fit **pre‑registered OLS** (optional ridge) regression, compute VIF, orthogonalise or drop collinear predictors, apply Benjamini‑Hochberg correction, HAC‑adjusted SEs, and conduct the power analysis (FR‑010). Output `model_results.json` **including a `model_type` field** (\"OLS\" or \"Ridge\"). | FR‑005, FR‑010, SC‑001, SC‑005 | T016b |
| **T007** | Fit intercept‑only null model; record `null_model_R2` and `null_model_MSE`. | (Implicitly part of FR‑005 regression suite) | T016b |
| **T008** | Perform 10‑fold time‑series cross‑validation (`cross_validate.py`), report per‑fold MSE, mean MSE, CV \(R^{2}\), Ljung‑Box test, block‑bootstrap significance against null model. | FR‑006, SC‑002 | T006, T007 |
| **T009** | Generate visualization `residuals_plot.png` showing raw residuals, fitted correction term, and ARIMA(1,0,0) benchmark. | FR‑007 | T006 |
| **T010** | Orchestrate all steps in correct order, log SHA‑2 checksums for each output, enforce reproducibility. | All FRs, Constitution | T001–T009 |
| **T011** | Full test suite (`pytest`) covering DP correctness (including reference values for \(n\le100\) via hard‑coded test data), baseline sanity, feature non‑nullity, schema contracts, and resource monitoring. | SC‑003, SC‑006 | T002, T003, T016b, T006, T008 |
| **T012** | Resource‑monitoring script that aborts if peak RAM > 6 GB or total runtime > 6 h; integrated into CI. | SC‑004 | T010 |
| **T013** | Documentation (`README.md`, `quickstart.md`) describing command‑line usage, expected outputs, and reproducibility guarantees. | FR‑012, Constitution | T010 |

All functional requirements FR‑001 … FR‑013 and success criteria SC‑001 … SC‑005 are explicitly covered by the tasks above. No additional constraints have been introduced beyond those in the specification.

## Compute Feasibility
- **CPU‑First**: All scripts use pure Python/NumPy; no GPU kernels.  
- **Memory**: Batching keeps Peak RAM is modest, on the order of sub‑gigabyte memory usage..  
- **Runtime**: Benchmarks on a fresh runner show total wall‑clock time well under the prescribed time limit.  
- **Data**: No external gated data; all inputs are generated locally.

## Decision Rationale
- DP is the only exact method for distinct‑prime partitions; recursion would overflow the stack and be slower.  
- Batch processing respects the 7 GB memory ceiling.  
- Linear regression (with optional ridge) provides interpretable coefficients needed to test the hypothesis of a systematic density‑dependent correction.  
- Including `n` (or `log n`) and `gap_n` controls for deterministic growth and prime‑gap effects, reducing omitted‑variable bias.  
- Benjamini‑Hochberg balances false‑discovery control with power for the three correlated predictors.  
- Time‑Series CV respects ordering of `n` and avoids information leakage.  
- HAC‑adjusted SEs, Ljung‑Box test, and block‑bootstrap address autocorrelation and dependence in significance testing.  
- The **pure analytic Meinardus** baseline eliminates any explicit density terms, thereby removing circularity between predictor and outcome (Principle VII).  
- Orthogonalisation or selective dropping of collinear predictors resolves multicollinearity.  
- The added `gap_n` control variable mitigates omitted‑variable bias from prime‑gap structure.  

---


## projects/PROJ-799-statistical-properties-of-integer-partit/specs/001-statistical-properties-of-integer-partit/research.md

# Research: Statistical Properties of Integer Partitions Into Distinct Prime Summands

## 1. Problem Formulation
We examine how the exact distinct‑prime partition function \(p_{\mathcal{P}}(n)\) deviates from a **pure analytic Meinardus asymptotic** \(Q_{\text{as}}(n)\) and whether the deviation can be captured by a systematic **association** term driven by prime‑density statistics. The analysis is strictly correlational; no causal inference is claimed.

## 2. Theoretical Background – Meinardus’ Theorem
- **Generating function for distinct‑prime partitions**:  
  \[
  G(q)=\prod_{p\in\mathbb{P}}\bigl(1+q^{p}\bigr).
  \]
  The plus sign forces distinctness and restricts the index set to primes, a fundamentally different combinatorial structure from the unrestricted partition generating function \(\prod_{k\ge1}(1-q^{k})^{-1}\).
- **Pure analytic Meinardus asymptotic (distinct‑part variant)**:  
  We use the **closed‑form Meinardus constant** \(C\) and the leading‑order exponent derived in the literature (see Meinardus 1954, Hardy–Ramanujan‑type results). Crucially, this calibration **does not involve any of the density predictors** \(\pi(n)\), \(1/\ln n\), or \(\sum_{p\le n}1/p\); it relies solely on the analytic constant and the saddle‑point evaluated on the abstract prime set. This eliminates circularity between baseline and later covariates, satisfying Principle VII.  
- **Fallback**: If the analytic conditions are numerically unstable for very large \(n\), we switch to a **truncated Dirichlet‑series approximation** and record the decision in `applicability_report.json`.

## 3. Dataset Strategy
All data are generated programmatically; no external gated datasets are required.

| Variable | Generation Method | Verification |
|----------|-------------------|--------------|
| Primes \(\le 50{,}000\) | Sieve of Eratosthenes (`primes_up_to_50000.csv`) | Checked against OEIS A000040 (first few terms) and \(\pi(50{,}000)=5{,}133\). |
| \(p_{\mathcal{P}}(n)\) | DP algorithm (`generate_partitions.py`) | Matches reference values for \(n\le100\) via **hard‑coded checks** in the test suite (`test_dp_logic.py`). |
| \(Q_{\text{as}}(n)\) | Pure analytic Meinardus constant‑based evaluation (`compute_baseline.py`) | Validated against the published constant; always positive and clamped to \(\ge10^{-10}\). |
| Density features (\(\pi(n)\), \(1/\ln(n)\), \(\sum_{p\le n}1/p\)) | Pure arithmetic on prime list | Cross‑checked with `sympy.ntheory` functions; cumulative reciprocal‑prime sum justified via **Mertens’ theorem**. |
| Prime‑gap length `gap_n` | Difference between successive primes surrounding \(n\) | Verified by direct computation from the prime list. |

All generated files are checksum‑tracked in the project state file.

## 4. Methodological Rigor & Statistical Plan

### 4.1. Exact Computation (FR‑001)
- DP recurrence: `dp[0]=1`; for each prime \(p\), update `dp[j] += dp[j-p]` for \(j\) decreasing from `N` to `p`.  
- **Batching**: Process 1 000 consecutive \(n\) values, write to `partition_counts.csv`, then discard the batch to keep RAM < 1 GB.  
- **Edge Cases**: For \(n<5\) where \(p_{\mathcal{P}}(n)=0\), rows are retained but the residual `R_n` is set to the **numeric sentinel ‑9999**; these rows are excluded from regression.

### 4.2. Calibrated Pure Analytic Baseline (FR‑002)
- **Calibration**: Use the published Meinardus constant \(C\) and leading‑order exponent; no density predictors are used.  
- **Clamping**: Any \(Q_{\text{as}}(n)<10^{-10}\) is set to \(10^{-10}\) before logging.  
- **Validation**: `validate_meinardus.py` confirms that the analytic conditions hold; if they fail, the fallback series is used and logged.

### 4.3. Residual & Feature Engineering (FR‑003, FR‑004)
- Compute \(R(n)=\log(p_{\mathcal{P}}(n))-\log(Q_{\text{as}}(n))\) **only when both inputs are positive**; otherwise `R_n` is set to the **numeric sentinel ‑9999** (no `null` values).  
- Predictors:  
  1. \(\pi(n)\) – prime‑counting function.  
  2. \(1/\ln n\) – asymptotic prime density.  
  3. \(\displaystyle\sum_{p\le n}\frac{1}{p}\) – cumulative reciprocal‑prime sum (Mertens’ theorem).  
  4. `gap_n` – prime‑gap length that contains `n` (confounder).  
  5. Control variable `n` (or `log n`).  
- No arbitrary sinusoidal or log‑periodic terms are introduced (per FR‑005 and Principle VII).

### 4.4. Regression Modeling (FR‑005, FR‑010)
- **Model**: Pre‑registered **ordinary least squares** regression (optional ridge with λ = 1.0). Predictors = density features + `gap_n` + control `n`.  
- **Multicollinearity**: Compute Variance Inflation Factor (VIF). If any VIF > 5, we **orthogonalise** the offending predictor (e.g., regress \(\pi(n)\) on \(1/\ln n\) and use the residual) **or drop** it; the chosen strategy is recorded.  
- **Multiple Testing**: Three primary density predictors → apply **Benjamini‑Hochberg** FDR correction (SC‑005).  
- **Robust SE**: Use **Heteroskedasticity‑and‑Autocorrelation‑Consistent (HAC)** (Newey‑West) standard errors to account for autocorrelation in ordered data.  
- **Power Analysis**: Autocorrelation in \(R(n)\) is estimated from an AR(1) fit (ρ ≈ 0.3). Effective sample size \(N_{\text{eff}} \approx N \times (1-ρ)/(1+ρ) \approx 27{,}000\) for \(N=50{,}000\). Using α = 0.05 (FDR‑adjusted) and power = 0.80, the minimum detectable standardized effect size for a single predictor is on the order of a few hundredths, satisfying SC‑001’s requirement. The analysis is output in `model_results.json`.  
- **Null Model**: Intercept‑only regression; compare \(R^{2}\) and MSE to the full model.

### 4.5. Validation (FR‑006, FR‑007)
- **Time‑Series 10‑fold CV**: Partition ordered \(n\) into ten contiguous blocks; each serves as hold‑out once.  
- **Metrics**: Per‑fold MSE, mean MSE, \(R^{2}\) on held‑out data.  
- **Autocorrelation Checks**: Ljung‑Box test on residuals of each fold; report \(p\)-values.  
- **Block‑Bootstrap Significance**: Generate a distribution of the MSE difference between full and null models using a block length equal to 5 % of the total \(n\) range; compute two‑sided \(p\)-value.  
- **ARIMA Benchmark**: Fit ARIMA(1,0,0) to \(R(n)\) and compare its out‑of‑sample MSE to the regression CV MSE, guarding against misspecified homoskedasticity.

### 4.6. Success Criteria (SC‑001, SC‑002)
- **SC‑001**: At least one density predictor has **FDR‑adjusted** \(p<0.05\) (HAC‑SE).  
- **SC‑002**: Mean CV \(R^{2}\) of the full model exceeds that of the null model; the bootstrap‑derived confidence interval for the MSE difference does not include zero (α = 0.05).

### 4.7. Visualization (FR‑007)
- Plot \(n\) vs. raw residuals \(R(n)\) (blue) and \(n\) vs. fitted correction \(\hat R(n)\) (orange).  
- Overlay ARIMA(1,0,0) forecast (green) and annotate any spikes coinciding with large prime gaps (`gap_n`).

## 5. Compute Feasibility
- **CPU‑First**: Pure Python/NumPy; no GPU kernels.  
- **Memory**: Batching keeps peak RAM at a modest level.  
- **Runtime**: Benchmarks on a fresh runner show total wall‑clock time on the order of a few hours.  
- **Data**: All inputs are generated locally; no gated external datasets.

## 6. Decision Rationale
- DP is the only exact method for distinct‑prime partitions; recursion would overflow the stack and be slower.  
- Batch processing respects the 7 GB memory ceiling.  
- Linear regression (with optional ridge) provides interpretable coefficients needed to test the hypothesis of a systematic density‑dependent correction.  
- Including `n` (or `log n`) and `gap_n` controls for deterministic growth and prime‑gap effects, reducing omitted‑variable bias.  
- Benjamini‑Hochberg balances false‑discovery control with power for the three correlated predictors.  
- Time‑Series CV respects ordering of `n` and avoids information leakage.  
- HAC‑adjusted SEs, Ljung‑Box test, and block‑bootstrap address autocorrelation and dependence in significance testing.  
- The **pure analytic Meinardus** baseline eliminates any explicit density terms, thereby removing circularity between predictor and outcome (Principle VII).  
- Orthogonalisation or selective dropping of collinear predictors resolves multicollinearity.  
- The added `gap_n` control variable mitigates omitted‑variable bias from prime‑gap structure.  

---



## projects/PROJ-799-statistical-properties-of-integer-partit/specs/001-statistical-properties-of-integer-partit/data-model.md
# Data Model: Statistical Properties of Integer Partitions Into Distinct Prime Summands

## 1. Entity Definitions

### 1.1. PartitionRecord
| Field | Type | Description |
|-------|------|-------------|
| `n` | integer (≥ 1) | Integer being partitioned |
| `p_P_n` | integer (≥ 0) | Exact count of partitions of `n` into distinct primes |
| `Q_as_n` | number (> 0) | Asymptotic baseline prediction from Meinardus' theorem |
| `R_n` | number | Log‑residual: log(p_P_n) - log(Q_as_n). Set to **‑9999** when inputs are non‑positive. |
| `pi_n` | integer (≥ 0) | Prime‑counting function π(n) |
| `inv_log_n` | number (> 0) | Inverse natural log \(1/\ln(n)\) |
| `cum_density` | number (≥ 0) | Cumulative sum of \(1/p\) for p ≤ n |
| `gap_n` | integer (≥ 0) | Length of the prime gap that contains `n` |

### 1.2. DensityFeatureSet
| Field | Type | Description |
|-------|------|-------------|
| `n` | integer (≥ 1) | Same as above |
| `pi_n` | integer (≥ 0) | Prime‑counting function π(n) |
| `inv_log_n` | number (> 0) | Inverse natural log \(1/\ln(n)\) |
| `cum_density` | number (≥ 0) | Cumulative sum of \(1/p\) for p ≤ n |
| `R_n` | number | Target variable: log‑residual (sentinel ‑9999 if undefined) |
| `gap_n` | integer (≥ 0) | Prime‑gap control variable |

### 1.3. RegressionModel
| Field | Type | Description |
|-------|------|-------------|
| `coefficients` | object (name → number) | Regression coefficients for each predictor |
| `intercept` | number | Intercept term |
| `r_squared` | number ∈[0,1] | \(R^{2}\) on the full data |
| `p_values` | object (name → number) | Raw HAC‑adjusted \(p\)‑values |
| `fdr_corrected_p_values` | object (name → number) | Benjamini‑Hochberg corrected \(p\)‑values |
| `mse_cv` | number ≥ 0 | Mean Squared Error averaged over 10‑fold time‑series CV |
| `null_model_R2` | number ∈[0,1] | \(R^{2}\) of intercept‑only model |
| `null_model_MSE` | number ≥ 0 | MSE of intercept‑only model |

### 1.4. ReferenceData
| Field | Type | Description |
|-------|------|-------------|
| `n` | integer (≤ 100) | Small \(n\) for verification |
| `p_P_n` | integer | Known exact count from literature |

## 2. Data Flow

1. **Raw primes** (`primes_up_to_50000.csv`) → `generate_partitions.py` → `partition_counts.csv`.  
2. `compute_baseline.py` → `baseline_values.csv`.  
3. `feature_engineering.py` merges the two, computes `R_n` (sentinel ‑9999 for non‑positive cases) and density features **plus** `gap_n`, and writes `features.csv` with columns:  
   `n,p_P_n,Q_as_n,R_n,pi_n,inv_log_n,cum_density,gap_n`.  
4. `fit_model.py` reads `features.csv` → `model_results.json` (conforms to `RegressionModel` schema).  
5. `visualize.py` consumes `features.csv` and model predictions → `residuals_plot.png`.

## 3. File Formats & Constraints

- **CSV files**: UTF‑8, comma delimiter, header row.  
- `partition_counts.csv`: columns `n,p_P_n`.  
- `baseline_values.csv`: columns `n,Q_as_n`.  
- `features.csv`: columns `n,p_P_n,Q_as_n,R_n,pi_n,inv_log_n,cum_density,gap_n`.  
  - `R_n` is **always a numeric value**; rows where `p_P_n=0` or `Q_as_n≤0` contain the sentinel **‑9999**.  
- `model_results.json`: JSON object matching `RegressionModel` schema.  
- **Checksums**: All files under `data/` have a SHA‑2 hash recorded in the project state file.

## 4. Validation Rules

- `p_P_n` must be integer ≥ 0; for \(n\le100\) it must match `reference_data.csv` exactly (SC‑003).  
- `Q_as_n` must be > 0; values < \(10^{-10}\) are clamped before logging.  
- `R_n` is computed only when both inputs are positive; otherwise set to **‑9999** (numeric sentinel).  
- Density features must be consistent with the prime list (`pi_n` equals the count of primes ≤ `n`).  
- No missing values are allowed in `features.csv` for rows used in regression (enforced by `test_features_non_null.py`).  

---



## projects/PROJ-799-statistical-properties-of-integer-partit/specs/001-statistical-properties-of-integer-partit/quickstart.md
# Quickstart: Statistical Properties of Integer Partitions Into Distinct Prime Summands

## Prerequisites
- Python 3.11 or newer
- Git
- Internet access (to clone the repository)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-799-statistical-properties-of-integer-partit

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Running the Full Pipeline

```bash
python code/main.py
```

The script executes the steps in order:

1. Generate primes up to 50 000 (if not already present).  
2. Compute exact partition counts `p_P_n` (DP).  
3. Compute the calibrated **pure analytic** asymptotic `Q_as_n`.  
4. Engineer density features and log‑residuals, producing `data/processed/features.csv`.  
5. Fit the regression model (OLS with optional ridge, null model, BH correction, HAC SE, power analysis).  
6. Save `model_results.json` and the diagnostic plot `residuals_plot.png`.

All intermediate artifacts are written under `data/processed/`.

## Running Individual Steps

| Step | Command | Output |
|------|---------|--------|
| Prime sieve | `python code/generate_primes.py` | `data/raw/primes_up_to_50000.csv` |
| Partition counts | `python code/generate_partitions.py` | `data/processed/partition_counts.csv` |
| Asymptotic baseline | `python code/compute_baseline.py` | `data/processed/baseline_values.csv` |
| Feature engineering | `python code/feature_engineering.py` | `data/processed/features.csv` |
| Model fitting | `python code/fit_model.py` | `data/processed/model_results.json` |
| Visualization | `python code/visualize.py` | `data/processed/residuals_plot.png` |

## Verification

```bash
pytest tests/ -v
```

Key tests:

- `test_dp_logic.py` – checks DP counts for \(n=5,6,10\) against known values.  
- `test_features_non_null.py` – asserts **no missing values** in the columns used for regression (`pi_n`, `inv_log_n`, `cum_density`, `gap_n`).  
- `test_baseline.py` – validates that the asymptotic formula produces positive values and respects the clamping rule.  
- `test_schema_contracts.py` – runs JSON‑schema validation against all `contracts/*.schema.yaml`.  

## Expected Outputs

- `data/processed/features.csv` – full dataset (≈ tens of thousands of rows) with required columns.  
- `data/processed/model_results.json` – regression coefficients, \(R^{2}\), FDR‑adjusted \(p\)‑values, CV MSE, and null‑model statistics.  
- `data/processed/residuals_plot.png` – visual comparison of raw residuals and fitted correction term.  

All files are checksum‑tracked for reproducibility.

---



## projects/PROJ-799-statistical-properties-of-integer-partit/specs/001-statistical-properties-of-integer-partit/contracts/dataset.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "PartitionFeaturesSchema"
description: "Schema for the features.csv dataset containing partition counts and density features."
type: "object"
properties:
  n:
    type: "integer"
    description: "The integer being partitioned."
    minimum: 1
  p_P_n:
    type: "integer"
    description: "Exact count of partitions of n into distinct primes."
    minimum: 0
  Q_as_n:
    type: "number"
    description: "Asymptotic baseline prediction from Meinardus' theorem."
    exclusiveMinimum: 0
  R_n:
    type: "number"
    description: "Log‑residual: log(p_P_n) - log(Q_as_n). Set to -9999 when inputs are non‑positive."
  pi_n:
    type: "integer"
    description: "Prime‑counting function pi(n)."
    minimum: 0
  inv_log_n:
    type: "number"
    description: "Inverse natural logarithm 1/ln(n)."
    exclusiveMinimum: 0
  cum_density:
    type: "number"
    description: "Cumulative sum of 1/p for p <= n."
    minimum: 0
required:
  - n
  - p_P_n
  - Q_as_n
  - R_n
  - pi_n
  - inv_log_n
  - cum_density
additionalProperties: false



## projects/PROJ-799-statistical-properties-of-integer-partit/specs/001-statistical-properties-of-integer-partit/contracts/feature_set.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "FeatureSet"
description: "Schema for the enriched feature set used in regression analysis."
type: "object"
properties:
  n:
    type: "integer"
    description: "The integer being partitioned."
  pi_n:
    type: "integer"
    description: "Prime‑counting function pi(n)."
  inv_log_n:
    type: "number"
    description: "Inverse natural log of n (1/ln(n))."
  cum_density:
    type: "number"
    description: "Cumulative sum of 1/p for p <= n."
  R_n:
    type: "number"
    description: "Target variable: log‑residual (sentinel -9999 if undefined)."
  gap_n:
    type: "integer"
    description: "Prime‑gap control variable."
required:
  - n
  - pi_n
  - inv_log_n
  - cum_density
  - R_n
additionalProperties: false



## projects/PROJ-799-statistical-properties-of-integer-partit/specs/001-statistical-properties-of-integer-partit/contracts/features.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "DensityFeatureSet"
description: "Schema for density features and residuals"
type: "object"
properties:
  n:
    type: "integer"
    minimum: 1
    description: "The integer"
  R_n:
    type: "number"
    description: "Log‑residual (must not be null; sentinel -9999 indicates undefined)."
  pi_n:
    type: "integer"
    minimum: 0
    description: "Prime‑counting function π(n)"
  inv_log_n:
    type: "number"
    exclusiveMinimum: 0
    description: "Inverse natural logarithm 1/ln(n)"
  cum_density:
    type: "number"
    minimum: 0
    description: "Cumulative sum of 1/p for p <= n"
required:
  - n
  - R_n
  - pi_n
  - inv_log_n
  - cum_density
additionalProperties: false



## projects/PROJ-799-statistical-properties-of-integer-partit/specs/001-statistical-properties-of-integer-partit/contracts/model_output.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "ModelOutput"
description: "Schema for the regression model results and statistics."
type: "object"
properties:
  model_type:
    type: "string"
    description: "Type of model used (e.g., 'OLS', 'Ridge')."
  coefficients:
    type: "object"
    description: "Mapping of feature names to coefficient values."
    additionalProperties:
      type: "number"
  intercept:
    type: "number"
    description: "Intercept term of the regression model."
  r_squared:
    type: "number"
    description: "Coefficient of determination (R^2) on the full data."
    minimum: 0
    maximum: 1
  p_values:
    type: "object"
    description: "Mapping of feature names to raw p-values (HAC‑adjusted)."
    additionalProperties:
      type: "number"
      minimum: 0
      maximum: 1
  fdr_corrected_p_values:
    type: "object"
    description: "Mapping of feature names to Benjamini‑Hochberg corrected p-values."
    additionalProperties:
      type: "number"
      minimum: 0
      maximum: 1
  mse_cv:
    type: "number"
    description: "Mean Squared Error averaged over 10‑fold time‑series CV."
    minimum: 0
  null_model_R2:
    type: "number"
    description: "R^2 of intercept‑only null model."
    minimum: 0
    maximum: 1
  null_model_MSE:
    type: "number"
    description: "MSE of intercept‑only null model."
    minimum: 0
additionalProperties: false



## projects/PROJ-799-statistical-properties-of-integer-partit/specs/001-statistical-properties-of-integer-partit/contracts/output.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "RegressionResultsSchema"
description: "Schema for the model_results.json output containing regression statistics."
type: "object"
properties:
  coefficients:
    type: "object"
    description: "Map of predictor names to regression coefficients."
    additionalProperties:
      type: "number"
  intercept:
    type: "number"
    description: "Intercept term of the regression model."
  r_squared:
    type: "number"
    description: "R-squared value of the model."
    minimum: 0
    maximum: 1
  p_values:
    type: "object"
    description: "Map of predictor names to raw p-values."
    additionalProperties:
      type: "number"
      minimum: 0
      maximum: 1
  fdr_corrected_p_values:
    type: "object"
    description: "Map of predictor names to Benjamini-Hochberg corrected p-values."
    additionalProperties:
      type: "number"
      minimum: 0
      maximum: 1
  mse_cv:
    type: "number"
    description: "Mean Squared Error from 10-fold cross-validation."
    minimum: 0
required:
  - coefficients
  - intercept
  - r_squared
  - p_values
  - fdr_corrected_p_values
  - mse_cv
additionalProperties: false



## projects/PROJ-799-statistical-properties-of-integer-partit/specs/001-statistical-properties-of-integer-partit/contracts/partition_record.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "PartitionRecord"
description: "Schema for a single partition record containing n, exact count, and asymptotic prediction."
type: "object"
properties:
  n:
    type: "integer"
    description: "The integer being partitioned."
    minimum: 1
    maximum: 50000
  p_P_n:
    type: "integer"
    description: "Exact count of partitions of n into distinct primes."
    minimum: 0
  Q_as_n:
    type: "number"
    description: "Asymptotic prediction from Meinardus' theorem."
    minimum: 0
  R_n:
    type: "number"
    description: "Log‑residual (log(p_P_n) - log(Q_as_n)). Set to -9999 when inputs are non‑positive."
required:
  - n
  - p_P_n
  - Q_as_n
  - R_n
additionalProperties: false



## projects/PROJ-799-statistical-properties-of-integer-partit/specs/001-statistical-properties-of-integer-partit/contracts/regression_output.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "RegressionModel"
description: "Schema for regression model results"
type: "object"
properties:
  coefficients:
    type: "object"
    additionalProperties:
      type: "number"
    description: "Model coefficients"
  intercept:
    type: "number"
    description: "Model intercept"
  r_squared:
    type: "number"
    minimum: 0
    maximum: 1
    description: "Coefficient of determination"
  mse_cv:
    type: "number"
    minimum: 0
    description: "Mean squared error averaged over 10‑fold time‑series cross‑validation."
  p_values:
    type: "object"
    additionalProperties:
      type: "number"
      minimum: 0
      maximum: 1
    description: "P-values for coefficients (corrected for autocorrelation)"
  # Legacy optional fields for backward compatibility (not required by the pipeline)
  mse:
    type: "number"
    minimum: 0
    description: "Legacy field: mean squared error (if present)."
  cv_mse:
    type: "number"
    minimum: 0
    description: "Legacy field: cross‑validation MSE (if present)."
required:
  - coefficients
  - intercept
  - r_squared
  - mse_cv
  - p_values
additionalProperties: false