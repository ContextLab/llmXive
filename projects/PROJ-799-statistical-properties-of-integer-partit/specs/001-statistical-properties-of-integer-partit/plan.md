# Implementation Plan: Statistical Properties of Integer Partitions Into Distinct Prime Summands

**Branch**: `001-statistical-properties-of-integer-partitions-into-distinct-prime-summands` | **Date**: 2026-07-10 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-statistical-properties-of-integer-partitions-into-distinct-prime-summands/spec.md`

## Summary

This project investigates the deviation of the partition function $p_{\mathcal{P}}(n)$ (counting partitions of $n$ into distinct primes) from the asymptotic predictions of Meinardus' theorem. The primary technical approach involves:
1.  **Exact Computation**: Using a memory-optimized dynamic programming algorithm to compute $p_{\mathcal{P}}(n)$ for $n$ up to 50,000. Due to the super-polynomial growth of the partition function, values will be computed and stored in batches or streamed to disk to avoid RAM overflow, rather than storing the full array in memory.
2.  **Theoretical Baseline**: Implementing the distinct-partition variant of Meinardus' theorem, explicitly validating its conditions (pole structure of the Prime Zeta function) and falling back to a truncated Dirichlet series if necessary.
3.  **Statistical Modeling**: Calculating log-residuals $R(n)$ and regressing them against *higher-order* prime density features to identify systematic correction terms, while explicitly avoiding circular predictors.
4.  **Validation**: Performing time-series cross-validation (blocking) and generating visualizations to assess model robustness.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `sympy`, `statsmodels`  
**Storage**: Local CSV/Parquet files in `data/` (checksummed); No external database.  
**Testing**: `pytest` with unit tests for DP logic, integration tests for the full pipeline, and contract tests against JSON schemas.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` free tier: 2 vCPU, 7GB RAM).  
**Project Type**: Computational mathematics research / CLI tool.  
**Performance Goals**: Complete full pipeline (generation to visualization) within 6 hours; Peak memory < 7GB (via batch processing).  
**Constraints**: No GPU required; must handle $n=50,000$ without integer overflow (using Python's arbitrary precision integers).  
**Scale/Scope**: $N=50,000$ data points; [deferred] primes to precompute.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence in Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | `requirements.txt` pins versions; random seeds fixed in `code/`; CI runs isolated. |
| **II. Verified Accuracy** | ✅ Pass | All citations (Meinardus, Prime Zeta) mapped to primary sources; no unverified URLs in plan. |
| **III. Data Hygiene** | ✅ Pass | `data/` files checksummed; derivations create new files; no in-place modification. |
| **IV. Single Source of Truth** | ✅ Pass | All stats trace to `data/processed/features.csv`; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | ✅ Pass | Artifacts carry content hashes; state updated on change. |
| **VI. Finite-Regime Error Term Precision** | ✅ Pass | Plan explicitly computes $R(n)$ for finite $n$; DP algorithm documented as exact (no approximation). |
| **VII. Density-Dependent Correlation Rigor** | ✅ Pass | Regression model avoids assuming linearity; uses only theoretically motivated density features; excludes arbitrary trigonometric terms; includes Null Model comparison. |

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-properties-of-integer-partitions-into-distinct-prime-summands/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── feature_set.schema.yaml
│   ├── features.schema.yaml
│   ├── model_output.schema.yaml
│   ├── output.schema.yaml
│   ├── partition_record.schema.yaml
│   ├── regression_output.schema.yaml
│   └── reference_data.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-799-statistical-properties-of-integer-partit/
├── code/
│   ├── __init__.py
│   ├── generate_partitions.py      # DP algorithm for p_P(n) with batch streaming
│   ├── compute_baseline.py         # Meinardus/Dirichlet baseline Q_as(n)
│   ├── validate_meinardus.py       # Checks pole conditions and generates applicability_report.json
│   ├── feature_engineering.py      # Density features and residuals
│   ├── fit_model.py                # Regression/GAM fitting with time-series CV
│   ├── visualize.py                # Plotting residuals and convergence
│   └── main.py                     # Pipeline orchestration
├── data/
│   ├── raw/
│   │   └── primes_up_to_50000.csv  # Precomputed primes (checksummed)
│   ├── processed/
│   │   ├── partition_counts.csv    # n, p_P(n) (streamed/batched)
│   │   ├── baseline_values.csv     # n, Q_as(n)
│   │   ├── features.csv            # n, p_P(n), Q_as(n), R(n), density features
│   │   └── reference_data.csv      # Reference values for n <= 100
│   └── reports/
│       └── applicability_report.json # Meinardus validation results
├── tests/
│   ├── unit/
│   │   ├── test_dp_logic.py
│   │   ├── test_baseline.py
│   │   └── test_features_non_null.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── contract/
│       └── test_schemas.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected for simplicity and direct data flow. No frontend/backend split required as this is a batch processing research pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Batch/Stream Processing** | $p_{\mathcal{P}}([deferred])$ has thousands of digits; storing all values in RAM exceeds 7GB. | A naive in-memory array would crash the runner. Streaming to disk or batch processing is required. |
| **Time-Series CV** | Residuals are sequential (autocorrelated). Standard K-fold CV would leak information. | Standard K-fold assumes i.i.d. data; blocking is required for valid p-values. |
| **Null Model Comparison** | To distinguish systematic correction from baseline approximation error. | Without a null model, any correlation with density features might be trivial. |

## Task Alignment

- **FR-001**: Implemented in `generate_partitions.py` with batch streaming.
- **FR-002**: Implemented in `compute_baseline.py` and `validate_meinardus.py` (fallback logic).
- **FR-003, FR-004, FR-005**: Implemented in `feature_engineering.py` (only valid density features).
- **FR-006**: Implemented in `fit_model.py` (Time-Series CV).
- **FR-007**: Implemented in `visualize.py`.
- **FR-008**: Implemented in `fit_model.py` (Null Model generation and comparison).
- **SC-003**: Supported by `reference_data.csv` and `test_features_non_null.py`.

## Compute Feasibility

- **CPU-First**: The DP algorithm is $O(N \cdot \pi(N))$. Operations on the order of $10^8$.
- **Memory Optimization**: Instead of storing all [deferred] large integers, the script computes values in batches (e.g., [deferred] at a time), writes to disk, and discards from RAM. This ensures peak memory usage remains well below 7GB.
- **GPU**: Not required.
- **Time Limit**: Estimated < 2 hours on free-tier runner.
