# Implementation Plan: Statistical Analysis of Flight Delay Distributions

**Branch**: `001-flight-delay-distributions` | **Date**: 2026-06-24 | **Spec**: `specs/001-flight-delay-distributions/spec.md`
**Input**: Feature specification from `/specs/001-flight-delay-distributions/spec.md`

## Summary

This project implements a statistical analysis pipeline to determine if flight delay times follow heavy-tailed distributions. The approach involves downloading Bureau of Transportation Statistics (BTS) data, cleaning it to produce a `total_delay_minutes` variable, fitting five parametric models (Exponential, Gamma, Log-Normal, Weibull, Pareto) via Maximum Likelihood Estimation (MLE), and performing heavy-tail diagnostics (Hill estimator, log-log survival plots) to validate the hypothesis. The implementation is constrained to CPU-only execution on GitHub Actions free-tier runners.

**Key Methodological Update**: The pipeline strictly separates bulk fit (AIC/BIC on `all_data`) from tail fit (Pareto/Hill on `positive_data` where x > x_min). Model selection requires passing a "Tail Validity Gate" (Tail KS test, Hill stability) before ranking by Bulk AIC. Zero-delay records are explicitly excluded from tail analysis to prevent bias. AIC comparisons are performed only on models fitted to the same dataset (`all_data`) to ensure N is consistent. If Pareto passes the Tail Validity Gate, it is compared against the best non-Pareto model using the Vuong Test to resolve the ranking gap.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scipy`, `numpy`, `matplotlib`, `requests`, `pyyaml`, `statsmodels` (for Vuong test)  
**Storage**: Local filesystem (`data/` for raw/processed CSVs, `output/` for plots/reports)  
**Testing**: `pytest` (unit tests for data cleaning, integration tests for fitting pipeline). **Mapping**:
  - `tests/test_cleaning.py`: Validates US-1 (Download, Parse, Filter, Zero Handling, Retention Rate).
  - `tests/test_fitting.py`: Validates US-2 (MLE, AIC/BIC, Vuong Test, Tail KS Test, x_min estimation).
  - `tests/test_diagnostics.py`: Validates US-3 (Hill Estimator, Stability, Log-Log R²).
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` free tier)  
**Project Type**: Data Analysis Script / CLI  
**Performance Goals**: Complete full analysis (download to plots) within 3600 seconds; Peak RAM ≤ 6.5 GB.  
**Constraints**: No GPU; no external API calls beyond dataset retrieval; strict adherence to BTS schema.  
**Scale/Scope**: Single year of US commercial flight data (approx. M+ records, filtered to ~5-7M valid records).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan mandates pinned `requirements.txt`, fixed random seeds, and deterministic data retrieval from verified URLs. |
| **II. Verified Accuracy** | PASS | Citations for datasets restricted to the `# Verified datasets` block. **No fallback to unverified data**; pipeline fails if full-year verified source is missing. Override arguments removed from CLI. |
| **III. Data Hygiene** | PASS | Plan includes checksumming of raw data (`data/raw/`) and immutable derivations (`data/processed/`). |
| **IV. Single Source of Truth** | PASS | All statistics in the final report will be generated directly from the `code/` execution, not hand-typed. |
| **V. Versioning Discipline** | PASS | Pipeline includes an explicit step (Task 3.4) to update `state/` files with artifact hashes upon successful run via `state_manager.py`. |
| **VI. Statistical Model Transparency** | PASS | Plan explicitly requires storing parameter estimates, AIC/BIC/KS/AD/Vuong metrics, and diagnostic plots for every fitted model. |
| **VII. Source Authenticity** | PASS | Data source is restricted to verified BTS HuggingFace mirrors for the full year as per the `# Verified datasets` block. |

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-analysis-of-publicly-availab/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── delay_record.schema.yaml
│   ├── fitted_model.schema.yaml
│   └── tail_index.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── raw/             # Downloaded raw BTS CSV/Parquet (checksummed)
│   └── processed/       # Cleaned delay data (total_delay_minutes)
├── src/
│   ├── __init__.py
│   ├── download.py      # Data retrieval and verification
│   ├── cleaning.py      # Pre-processing (US-1, Zero handling, Retention check)
│   ├── fitting.py       # MLE fitting, x_min estimation, Vuong/Tail KS tests (US-2)
│   ├── diagnostics.py   # Hill estimator, Log-Log R², Plots (US-3)
│   ├── main.py          # Orchestration script
│   └── state_manager.py # Updates state/ files (Principle V)
├── tests/
│   ├── test_cleaning.py
│   ├── test_fitting.py
│   └── test_diagnostics.py
├── output/              # Generated plots and JSON reports
└── requirements.txt     # Pinned dependencies
```

**Structure Decision**: Single project structure under `code/` with clear separation of concerns (download, cleaning, fitting, diagnostics). This minimizes overhead and ensures the entire pipeline runs in a single Python process to manage memory efficiently on the 7GB RAM limit.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Hill Estimator Stability Analysis** | Required by FR-005 to select `k` based on stability, not a fixed heuristic. | A fixed threshold is insufficient for rigorous heavy-tail confirmation and violates the spec's methodological requirement. |
| **Multiple Distribution Fitting** | Required by FR-003 to compare heavy vs. short-tailed models. | Fitting only one model (e.g., Pareto) would fail to provide the comparative evidence needed to answer the research question. |
| **In-memory Processing** | Required by Assumption about computational limits to ensure speed. | Chunked processing adds complexity and overhead; the spec assumes the dataset fits in RAM after filtering, allowing for faster vectorized operations in `pandas`/`numpy`. |
| **Tail vs. Bulk Decoupling** | Required by Scientific Soundness concerns to avoid false positives. | Using only AIC/BIC on the full dataset is dominated by the bulk and fails to detect tail behavior; decoupling is necessary for validity. |
| **Vuong Test** | Required by Methodology concerns to compare non-nested models. | AIC alone cannot statistically validate if one non-nested model is significantly better than another. |

## Implementation Phases

### Phase 0: Data Acquisition & Validation
- **Task 0.1**: Download BTS 2022 full-year data from verified HuggingFace URL.
- **Task 0.2**: Verify checksum and format.
- **Task 0.3**: **Retention Check**: Calculate `valid_records / total_records`. If < 95%, fail pipeline (SC-001).

### Phase 1: Pre-processing
- **Task 1.1**: Filter for commercial flights, handle missing values (treat as 0).
- **Task 1.2**: Compute `total_delay_minutes`.
- **Task 1.3**: **Zero Separation**: Create two datasets: `dataset_all` (includes 0s) and `dataset_positive` (filters `delay > 0`). `dataset_all` is used for Bulk AIC/BIC; `dataset_positive` is used for Tail Analysis (Hill, Pareto, Tail KS).
- **Task 1.4**: **Component vs. Sum Analysis**: Generate side-by-side plots and stats for `ArrDelay`, `DepDelay`, and `Sum` (FR-002). **Explicitly compare tail indices (Hill estimates) and tail shapes between the Sum and individual components** to distinguish shape from magnitude effects.

### Phase 2: Parametric Fitting & Model Selection
- **Task 2.1**: Fit Exponential, Gamma, Log-Normal, Weibull to `dataset_all`.
- **Task 2.2**: **Pareto Fitting**: Estimate `x_min` via KS minimization on `dataset_positive`, then fit Pareto to `x > x_min`. **This `x_min` is stored for use in the Tail Validity Gate for ALL models.**
- **Task 2.3**: Calculate Bulk AIC/BIC for all models (Exponential, Gamma, Log-Normal, Weibull) on `dataset_all`. **Pareto is excluded from this specific ranking** as it is fitted to a different subset.
- **Task 2.4**: **Tail Validity Gate**:
  - Perform Tail KS test on `x > x_min` (using the `x_min` from Task 2.2) for ALL models (including Exponential, Gamma, Log-Normal, Weibull, and Pareto).
  - Perform Hill stability analysis on `x > x_min`.
  - Discard models failing Tail KS (p < 0.05) or Hill stability.
- **Task 2.5**: **Vuong Test**: Compare top candidates (e.g., Log-Normal vs. Pareto) for statistical significance.
- **Task 2.6**: **Select final model**:
  1. Filter: Discard any model that fails the Tail Validity Gate.
  2. If Pareto passes the gate: Compare Pareto vs. the best non-Pareto model (lowest Bulk AIC) using the Vuong Test. If Vuong favors Pareto, select Pareto. Otherwise, select the best non-Pareto model.
  3. If Pareto fails the gate: Select the model with the lowest Bulk AIC among the remaining valid non-Pareto models.

### Phase 3: Diagnostics & Reporting
- **Task 3.1**: Generate Log-Log Survival Plot for best model.
- **Task 3.2**: **Calculate R²** of the log-log linear fit. **Explicitly report R² and check against 0.95 threshold (SC-004).**
- **Task 3.3**: Generate QQ-plots.
- **Task 3.4**: **State Update**: Update `state/` file with artifact hashes (Constitution Principle V) via `state_manager.py`.

## Risk Management

| Risk | Mitigation |
| :--- | :--- |
| **Dataset URL Change** | Pipeline fails gracefully with "Source Unavailable" error rather than using unverified fallback. |
| **Pareto Convergence Failure** | `x_min` estimation ensures valid fitting region; if still fails, model is excluded from selection. |
| **Memory Overflow** | Use `dtype` optimization in pandas; drop columns immediately after use. |
| **Zero-Spike Bias** | Explicit separation of `dataset_all` (for bulk fit) and `dataset_positive` (for tail fit). |
| **AIC Incomparability** | Bulk AIC comparison restricted to models fitted on `dataset_all`. Pareto is compared via Vuong Test if it passes the Tail Validity Gate. |