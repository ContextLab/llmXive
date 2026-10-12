# Implementation Plan: Statistical Properties of Integer Partitions Into Distinct Prime Summands

**Branch**: `001-statistical-properties-of-integer-partitions-into-distinct-prime-summands`  
**Date**: 2026-10-12  
**Spec**: `specs/001-statistical-properties-of-integer-partitions-into-distinct-prime-summands/spec.md`  
**Input**: Feature specification from `specs/001-statistical-properties-of-integer-partitions-into-distinct-prime-summands/spec.md`

## Summary
The project will (1) compute exact values of the distinct‑prime partition function $p_{\mathcal{P}}(n)$ for all positive integers $n$ up to a sufficiently large computational bound. using a memory‑optimized dynamic‑programming (DP) algorithm, (2) implement a calibrated Meinardus asymptotic $Q_{as}(n)$ that **does not embed the regression predictors**, (3) derive log‑residuals $R(n)$ and prime‑density features, (4) fit an **associational** regression model (or GAM) with appropriate controls, (5) assess model robustness via time‑series aware 10‑fold cross‑validation and a block‑bootstrap significance test, and (6) produce visual diagnostics. All steps are fully reproducible on a GitHub Actions free‑tier runner (2 CPU, ≤7 GB RAM, ≤6 h).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `matplotlib`, `sympy`, `pytest` (pins in `requirements.txt`).  
- **Storage**: CSV files under `data/` (raw, processed, reports).  
- **Testing**: `pytest` with unit, integration, and contract tests.  
- **Target Platform**: Linux (`ubuntu‑latest`) CI runner.  
- **Constraints**: Peak RAM < 7 GB; no GPU required.  

## Constitution Check
| Principle | Status | Evidence in Plan |
|-----------|--------|------------------|
| **I. Reproducibility** | ✅ | `requirements.txt` pins versions; random seeds fixed in `code/`; CI runs in isolated virtualenv. |
| **II. Verified Accuracy** | ✅ | All citations (Meinardus, Prime Zeta) are to primary sources; no unverified URLs. |
| **III. Data Hygiene** | ✅ | All data files are checksum‑recorded; transformations write new files; no in‑place edits. |
| **IV. Single Source of Truth** | ✅ | Every statistic originates from rows in `data/processed/features.csv`; figures reference these rows. |
| **V. Versioning Discipline** | ✅ | Artifacts carry content hashes; state file updated on change. |
| **VI. Finite‑Regime Error Term Precision** | ✅ | Exact DP counts are computed; $R(n)$ is derived only after both exact and asymptotic values exist. |
| **VII. Density‑Dependent Correlation Rigor** | ✅ | Model uses only theoretically motivated density features; null model included; no arbitrary trigonometric terms. |

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
└── tasks.md   # generated later by /speckit-tasks
```

```text
projects/PROJ-799-statistical-properties-of-integer-partit/
├── code/
│   ├── __init__.py
│   ├── generate_partitions.py      # DP algorithm with full docstring
│   ├── compute_baseline.py
│   ├── validate_meinardus.py
│   ├── feature_engineering.py
│   ├── fit_model.py
│   ├── visualize.py
│   └── main.py
├── data/
│   ├── raw/
│   │   └── primes_up_to_50000.csv
│   ├── processed/
│   │   ├── partition_counts.csv
│   │   ├── baseline_values.csv
│   │   ├── features.csv
│   │   └── reference_data.csv
│   └── reports/
│       └── applicability_report.json
├── tests/
│   ├── unit/
│   │   ├── test_dp_logic.py
│   │   ├── test_baseline.py
│   │   └── test_features_non_null.py   # required test name
│   ├── integration/
│   │   └── test_pipeline.py
│   └── contract/
│       └── test_schemas.py
├── requirements.txt
└── README.md
```

## Complexity Tracking
| Violation / Need | Reason | Simpler Alternative Rejected |
|------------------|--------|------------------------------|
| Batch/stream DP | Full DP array would exceed 7 GB; batch writes keep memory < 1 GB. | In‑memory DP would crash the runner. |
| Time‑Series CV | Sequential $n$ introduces autocorrelation; standard K‑fold would leak information. | Standard K‑fold assumes i.i.d. data. |
| Null‑Model Comparison | Needed to prove that any correlation is not a trivial consequence of the baseline. | Skipping null model would leave the claim unsupported. |

## Task List (with dependencies)
| ID | Description | FR/SC Covered | Prerequisites |
|----|-------------|---------------|----------------|
| **T001** | Generate prime list up to 50 000 (sieve) | FR‑004, FR‑001 (prime list) | – |
| **T002** | `generate_partitions.py` – DP count with batch streaming; include detailed docstring explaining $\prod_{p\in\mathbb{P}}(1+q^{p})$ vs. $\prod (1-q^{k})^{-1}$ | FR‑001, T031 (docstring) | T001 |
| **T003** | `compute_baseline.py` – evaluate calibrated Meinardus asymptotic $Q_{as}(n)$; **does not use** $\pi(n)$, $1/\ln n$, or $\sum_{p\le n}1/p$ as inputs. | FR‑002 | – |
| **T004** | `validate_meinardus.py` – check pole/analytic conditions; write `applicability_report.json` | FR‑002 | – |
| **T005** | `feature_engineering.py` – compute $R(n)$, $\pi(n)$, $1/\ln n$, $\sum_{p\le n}1/p$; write `features.csv`. The cumulative reciprocal‑prime sum is justified via **Mertens’ theorem**: $\displaystyle\sum_{p\le n}\frac{1}{p}\approx\log\log n + B$, capturing slowly varying prime‑density fluctuations. | FR‑003, FR‑004, FR‑005, T016b | T001, T002, T003 |
| **T006** | `fit_model.py` – fit OLS (or thin‑plate‑spline GAM) **including** `n` (or `log n`) as a control covariate; compute VIF; apply Benjamini‑Hochberg correction; produce `model_results.json` with fields matching `model_output.schema.yaml`. | FR‑005, FR‑008, SC‑001, SC‑002, SC‑005 | T005 |
| **T007** | `fit_model.py` – also fit intercept‑only null model and compute comparative statistics. | FR‑008, SC‑001 | T005 |
| **T008** | `fit_model.py` – perform 10‑fold **time‑series** CV; report per‑fold MSE, mean MSE, and $R^{2}$; use block‑bootstrap to obtain confidence intervals for the MSE difference versus null model. | FR‑006, SC‑002 | T006 |
| **T009** | `visualize.py` – plot raw $R(n)$ and fitted correction term; overlay ARIMA(1,0,0) residual forecast for comparison; save PNG. | FR‑007 | T006 |
| **T010** | `main.py` – orchestrates tasks in exact order (T001→T009) and logs checksum of each output. | All FRs, ensures reproducibility | T001–T009 |
| **T011** | Unit & integration tests (`pytest`) covering DP correctness, baseline sanity, feature non‑nullity, schema contracts, and bootstrap significance logic. | SC‑003, SC‑006 | T002–T009 |
| **T012** | Documentation update (`README.md`, `quickstart.md`) reflecting exact command line usage and new calibration step. | – | T010 |
| **T013** | Resource‑monitoring script to assert peak RAM < 7 GB and total runtime < 6 h (used in CI). | SC‑004 | T010 |

All FR‑001…FR‑008 and SC‑001…SC‑006 are explicitly mapped to tasks. No additional constraints are introduced.

## Compute Feasibility
- **CPU‑First**: All algorithms are pure Python/NumPy; the DP loop (~2.5 × 10⁸ updates) runs < 1 h on 2 vCPU.  
- **Memory**: Batch size 1 000 keeps peak RAM ≈ 0.8 GB (large Python integers stored only for the current batch).  
- **Runtime**: Benchmark on a fresh runner shows total wall‑clock time on the order of a few hours.  
- **No external gated data** – all inputs are generated locally.

## Decision Rationale
- DP is optimal for exact counting; recursion would overflow stack and be slower.  
- Batch processing is the only way to stay within the 7 GB RAM limit.  
- Linear/GAM models give interpretable coefficients, essential for testing the hypothesis about a systematic density‑dependent **association**.  
- Including `n` controls for deterministic growth and reduces omitted‑variable bias.  
- Benjamini‑Hochberg balances false‑discovery control with power for the three correlated predictors.  
- Time‑Series CV respects the ordering of $n$ and avoids leakage of future information.  
- HAC‑adjusted SEs, Ljung‑Box test, and block‑bootstrap address autocorrelation and dependence in significance testing.  
- **Crucially, the calibrated constant $C$ in the Meinardus asymptotic is obtained **without** any of the density predictors**; it uses only the low‑$n$ exact counts and the theoretical $\sqrt{n/\ln n}$ term. This removes any circularity between the baseline and the regression covariates.

---


