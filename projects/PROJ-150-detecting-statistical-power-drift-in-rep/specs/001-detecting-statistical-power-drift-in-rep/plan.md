# Implementation Plan: Detecting Statistical Power Drift in Replicated Studies

**Branch**: `001-detect-power-drift` | **Date**: 2024-05-21 | **Spec**: `specs/001-detecting-statistical-power-drift-in-rep/spec.md`
**Input**: Feature specification from `/specs/001-detecting-statistical-power-drift-in-rep/spec.md`

## Summary

This project investigates whether reported statistical power estimates in published replication studies exhibit a systematic temporal decline. The primary approach involves calculating post-hoc power for each study using reported effect sizes and sample sizes, then fitting a **Linear Mixed-Effects Model (LMM)** with `power_est` as the outcome, `year` as a fixed effect, and `effect_size` and `sample_size` as covariates. This model statistically isolates the temporal trend in power *after* accounting for the variance explained by changes in effect size and sample size, directly addressing the hypothesis of "residual drift" without tautology. The implementation will utilize a two-stage analytical pipeline: first, calculating power estimates; second, fitting the LMM and performing robustness checks (permutation tests, sensitivity analysis). This approach satisfies the core functional requirements (FR-002, FR-003) and Constitution Principle VII.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`  
**Storage**: Local filesystem (CSV/Parquet inputs, derived CSV/JSON outputs)  
**Testing**: `pytest` (unit tests for power formulas, integration tests for pipeline stages)  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, 7GB RAM)  
**Project Type**: Data analysis pipeline / CLI  
**Performance Goals**: Complete full pipeline (10k permutations) within 6 hours on CPU; memory usage < 6GB.  
**Constraints**: No GPU; must handle missing data gracefully; must use only open, directly downloadable datasets.  
**Scale/Scope**: Analysis of a large-scale set of replication studies from OSF Reproducibility Project dataset.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | All random seeds will be pinned in `code/`; datasets fetched from verified OSF/HuggingFace URLs; `requirements.txt` will pin versions. |
| **II. Verified Accuracy** | ✅ Pass | Citations in `research.md` will be limited to the verified dataset URLs provided in the prompt; no fabricated URLs. |
| **III. Data Hygiene** | ✅ Pass | Raw data will be checksummed in `state/`; derived data written to new files in `data/derived/`. |
| **IV. Single Source of Truth** | ✅ Pass | All figures and stats in the final report will trace to specific rows in `data/derived/` and code blocks in `code/`. |
| **V. Versioning Discipline** | ✅ Pass | Content hashes for artifacts will be managed via the project state file; `updated_at` timestamps updated on change. |
| **VI. Power Re-estimation Consistency** | ✅ Pass | Power estimates will be calculated post-hoc using Cohen's *d* and sample sizes with α=0.05, per the methodology. |
| **VII. Temporal Drift Modeling Rigor** | ✅ Pass | The plan implements the **Linear Mixed-Effects Model** with `power_est` as outcome and `year` as fixed effect, supplemented by non-parametric permutation tests with a sufficient number of iterations as required. |

## Project Structure

### Documentation (this feature)

```text
specs/001-detect-power-drift/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── power_calc.py          # Power formula implementation
│   ├── drift_model.py         # LMM implementation and LRT logic
│   └── permutation.py         # Permutation test logic
├── services/
│   ├── data_loader.py         # Dataset ingestion and cleaning
│   ├── analysis_runner.py     # Orchestration of analysis steps
│   └── viz.py                 # Visualization generation
├── cli/
│   └── main.py                # Entry point for CLI commands
└── lib/
    └── utils.py               # Common utilities (logging, seeding)

tests/
├── contract/
│   └── test_schemas.py        # Contract validation tests
├── integration/
│   └── test_pipeline.py       # End-to-end pipeline tests
└── unit/
    ├── test_power_calc.py
    └── test_permutation.py

data/
├── raw/                       # Downloaded datasets (immutable)
└── derived/                   # Calculated power, trends, results
```

**Structure Decision**: Selected Option 1 (Single project) with a modular `src/` layout. This aligns with the CLI nature of the analysis pipeline and facilitates unit testing of statistical formulas.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Linear Mixed-Effects Model (LMM)** | Required by FR-002 and Constitution Principle VII to statistically isolate the `year` effect on power while controlling for `effect_size` and `sample_size`. | A simple linear regression would fail to account for clustering (field, original study), violating the mixed-effects requirement. |
| **Permutations** | Required by the spec (FR-004) and Constitution Principle VII to ensure robustness against model misspecification. | A lower iteration count (e.g., [deferred]) would provide a coarser p-value estimate, potentially failing to detect subtle drift or robustness issues. |
| **Adaptive Weighting (DerSimonian-Laird)** | Required by FR-006 to handle heterogeneous effect-size metrics across fields. | Simple averaging would ignore field-specific variance and heterogeneity, biasing the aggregated drift estimate. |

## Implementation Phases & Tasks

### Phase 0: Data Acquisition & Validation
- **T001**: Create project structure and virtual environment.
- **T002**: Download the OSF Reproducibility Project dataset from the verified HuggingFace URL.
- **T003**: Validate dataset schema (presence of `year`, `effect_size`, `sample_size`, `field`).
- **T004**: Checksum raw data and store in `data/raw/`.

### Phase 1: Power Calculation & Preprocessing
- **T010**: Implement `calculate_power()` using the non-central t-distribution formula (FR-001).
- **T011**: Filter rows with missing `year`, `effect_size`, or `sample_size` (FR-008). Log warnings.
- **T012**: Generate `data/derived/power_estimates.csv` with `study_id`, `year`, `field`, `effect_size`, `sample_size`, `power_est`.

### Phase 2: Core Drift Analysis (LMM)
- **T013**: Implement `fit_lmm()` to fit `power_est ~ year + effect_size + sample_size + (1|field)` (FR-002).
- **T014**: Implement Likelihood-Ratio Test (LRT) comparing full model vs. reduced model (`power_est ~ effect_size + sample_size + (1|field)`) to test the `year` coefficient (FR-003).
- **T015**: Generate `results/lmm_summary.json` with slope, SE, p-value, and confidence intervals.
- **T016**: Generate `data/derived/residuals.csv` containing the residuals from the LMM (observed - predicted) for visualization.

### Phase 3: Robustness & Validation
- **T020**: Implement `run_permutation_test` with a sufficient number of iterations to ensure robust statistical power. (fallback to [deferred] on timeout). Shuffle `year` labels or permute residuals to generate null distribution of the `year` slope (FR-004, FR-007).
- **T021**: Generate `results/null_distribution.csv` with the permutation results.
- **T022**: Implement `sensitivity_analysis()` sweeping alpha {0.01, 0.05, 0.1} (FR-005).
- **T023**: Generate `results/sensitivity_report.json`.

### Phase 4: Cross-Field Aggregation & Visualization
- **T026**: Implement `aggregate_fields()` using DerSimonian-Laird on field-specific `year` slopes (FR-006).
- **T027**: Generate `results/aggregated_drift.json`.
- **T028**: Implement `generate_plots()` to visualize residual power vs. year (FR-009).
- **T029**: Generate `results/power_drift_scatter.png`.

### Phase 5: Reporting & Cleanup
- **T030**: Generate final `results/final_report.md`.
- **T035**: Run `ruff`/`black` for code cleanup and linting; ensure all tests pass.

## Compute Feasibility

- **CPU-First**: All statistical modeling (`statsmodels`), power calculations (`scipy`), and permutations (vectorized `numpy`) are CPU-tractable.
- **Memory**: The dataset (a moderate number of rows) fits easily in 7GB RAM. Permutation tests will use streaming or chunked processing to avoid memory spikes.
- **Runtime**: A large number of permutations on 2 cores may take several hours. The 6-hour CI limit is sufficient.
- **No GPU Required**: No deep learning models are involved; all methods are classical statistics.

## Risk Mitigation

- **Missing Data**: Rows with missing critical fields are excluded. A summary count is written to the log.
- **Zero Variance**: If a field has only one study, the random effect is collapsed to a fixed effect or the field is excluded from the mixed model.
- **Outliers**: Effect sizes with infinite variance or sample sizes < 2 are capped or filtered.
- **Permutation Timeout**: If the permutation loop exceeds a time threshold, it terminates early, flags the result as "approximate", and uses the available iterations.
- **Winner's Curse Bias**: A sensitivity analysis will be performed to assess if the drift is driven by publication bias (significant vs. non-significant results).