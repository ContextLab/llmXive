# Implementation Plan: Detecting Statistical Power Drift in Replicated Studies

**Branch**: `001-detect-power-drift` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-detecting-statistical-power-drift-in-rep/spec.md`

## Summary

This feature implements a statistical analysis pipeline to detect temporal drift in statistical power estimates within replicated studies. The core approach involves:
1.  **Power Re-estimation**: Calculating post-hoc power for each study based on reported effect sizes and sample sizes.
2.  **Residualization**: Removing the deterministic influence of effect size and sample size from the power estimate to create `power_residual`. This step is critical to avoid mathematical tautology.
3.  **Drift Modeling**: Fitting a Linear Mixed-Effects Model (LMM) on `power_residual` using only `year` as a fixed effect (and random intercepts for `field` and `original_study_id`) to isolate the residual temporal trend.
4.  **Robustness**: Validating the drift via permutation tests (shuffling `year`), input permutation tests (shuffling inputs), sensitivity analysis, and cross-field aggregation.

All data processing and modeling are designed to run on a CPU-only GitHub Actions runner, with streaming capabilities for large datasets and fallback mechanisms for permutation convergence.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels` (for LMM), `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `huggingface_hub`, `jsonschema`  
**Storage**: Local file system (`data/`, `results/`, `code/`)  
**Testing**: `pytest` (unit tests for power calculation, integration tests for pipeline flow). **All JSON/CSV outputs are validated against schemas defined in `contracts/`** (e.g., `aggregated_drift.schema.yaml`, `field_slopes.schema.yaml`).  
**Target Platform**: Linux (GitHub Actions Free Runner: multiple CPU cores, ~ GB RAM)  
**Project Type**: Data Analysis Pipeline / CLI  
**Performance Goals**: Complete full pipeline (including 1,000-10,000 permutations) within 6 hours on 2 cores; memory usage < 6 GB.  
**Constraints**: No GPU; CPU-first algorithms; streaming data ingestion to avoid OOM; strict reproducibility via pinned seeds.  
**Scale/Scope**: Process a substantial set of replication records (OSF data); generate multiple statistical outputs and multiple visualizations.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **[PRINCIPLE I: Reproducibility]**: The plan mandates pinned `requirements.txt`, explicit random seeds in `code/`, and a `data/` directory structure where raw data is checksummed and derived data is immutable. The pipeline will be tested on a fresh runner.
- **[PRINCIPLE II: Verified Accuracy]**: All citations to power formulas () and aggregation methods (DerSimonian-Laird) will be validated against primary sources before implementation. The `research.md` will cite only verified dataset URLs.
- **[PRINCIPLE III: Data Hygiene]**: The plan explicitly includes T011a (filtering missing data) and T011d (schema validation). No in-place modifications are allowed.
- **[PRINCIPLE IV: Single Source of Truth]**: All figures and statistics in the final report will be generated directly from `results/` JSON/CSV files produced by the code, ensuring no hand-typed numbers.
- **[PRINCIPLE V: Versioning Discipline]**: T032 is executed at the end of **every phase** to update `state.yaml` with content hashes and timestamps for all artifacts generated in that phase.
- **[PRINCIPLE VI: Power Re-estimation Consistency]**: The core logic (FR-001) strictly calculates post-hoc power using Cohen's *d* and sample size with α=0.05, ignoring author-reported power values.
- **[PRINCIPLE VII: Temporal Drift Modeling Rigor]**: The plan implements the dual-approach requirement: LMM with random intercepts for `field` and `original_study`, plus a permutation test with a sufficient number of iterations to ensure statistical stability to validate the slope.

## Project Structure

### Documentation (this feature)

```text
specs/001-detecting-statistical-power-drift-in-rep/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-150-detecting-statistical-power-drift-in-rep/
├── data/
│   ├── raw/                 # Downloaded parquet/CSV files (gitignored)
│   └── derived/             # Cleaned data, residuals, validation JSONs
├── code/
│   ├── __init__.py
│   ├── config.py            # Paths, seeds, constants
│   ├── preprocess.py        # T011a, T011b, T011c, T011d: Cleaning, grouping, schema validation
│   ├── power_calc.py        # FR-001: Post-hoc power formulas
│   ├── models.py            # T010, T012: MDES calc, LMM fitting, residual extraction
│   ├── robustness.py        # T020, T021, T025, T026, T027, T028: Permutations, sensitivity, aggregation, non-linearity
│   ├── visualize.py         # T013: Residual plots
│   ├── state_manager.py     # T032: State updates
│   └── main.py              # Pipeline orchestrator
├── tests/
│   ├── unit/
│   └── integration/
├── results/                 # JSON/CSV outputs for reports
├── state/
│   └── projects/PROJ-150-detecting-statistical-power-drift-in-rep/
│       └── state.yaml
├── requirements.txt
└── .gitignore
```

**Structure Decision**: Single project structure chosen to align with the data analysis pipeline nature. The `code/` directory is split into modular scripts corresponding to the task phases (Preprocessing, Modeling, Robustness) to facilitate unit testing and parallel development. `data/` is strictly separated into `raw` (immutable) and `derived` (intermediate).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Linear Mixed-Effects Model (LMM) | Required by FR-002 (revised) and Constitution Principle VII to control for `field` and `original_study` heterogeneity while testing `year` drift on residuals. | Ordinary Least Squares (OLS) would ignore clustering, inflating Type I error rates due to correlated errors within fields/studies. |
| Non-parametric Permutation Test | Required by FR-004 and Principle VII to validate the LMM slope against model misspecification without distributional assumptions. | Relying solely on parametric p-values is insufficient for robust scientific claims in observational data. |
| DerSimonian-Laird Aggregation | Required by FR-006 to combine field-specific estimates while accounting for heterogeneity in effect-size metrics. | Simple averaging would ignore variance differences between fields, biasing the global estimate. |
| Residualization (T011c) | Required to break the mathematical tautology of predicting Power using its own inputs. | Directly modeling Power ~ Year + Inputs creates perfect collinearity and uninterpretable coefficients. |

## Implementation Tasks

### Phase 0: Research & Feasibility
- [x] **T001a**: Initialize project directory structure (`data/raw`, `data/derived`, `code`, `tests`, `results`, `state`).
- [x] **T001b**: Create `.gitignore` excluding `data/raw`, `data/derived`, `__pycache__`, `.env`, and `*.pyc`.
- [x] **T002**: Finalize `research.md` with verified dataset URLs and methodology.

### Phase 1: Data Preparation & Pilot Analysis
- [ ] **T011a**: **Preprocessing & Power Calculation**.
  - Download OSF dataset (streaming if >100MB).
  - Filter rows with missing `year`, `effect_size`, or `sample_size`. Log warnings.
  - Calculate `power_estimate` using FR-001 formulas.
  - **Generate `data/derived/cleaned_data.csv`**: Output the cleaned dataset with the `power_estimate` column.
  - Output: `data/derived/cleaned_data.csv`.
- [ ] **T011b**: **Grouping Validation**.
  - Check unique levels of `field` and `original_study_id`.
  - Calculate variance of `power_estimate` per group. Flag groups with zero variance.
  - Output: `data/derived/grouping_validation.json`.
- [ ] **T011c**: **Residualization & Model Fitting**.
  - Fit a pilot OLS model: `power_estimate ~ year + effect_size + sample_size` to capture the deterministic relationship.
  - Calculate `power_residual = power_estimate - predicted_power` from this pilot model.
  - **Generate `data/derived/residuals.csv`**: Contains `study_id`, `year`, `field`, `original_study_id`, `power_residual`.
  - Fit the primary LMM: `power_residual ~ year + (1|field) + (1|original_study_id)`.
  - **Conditional Step**: If T011b detected significant field composition shifts, refit with `+ field_proportion`.
  - Output: `data/derived/residuals.csv`, `results/lmm_final_summary.json`.
- [ ] **T011d**: **Data Schema Validation**.
  - Verify presence of `year`, `effect_size`, `sample_size`, `field` in the downloaded dataset.
  - Halt with error if columns are missing.
  - Output: `data/derived/schema_validation.json`.
- [ ] **T010**: **Pilot MDES Calculation**.
  - Calculate Minimum Detectable Effect Size (MDES) for the `year` slope based on observed residual variance from T011c.
  - Output: `results/pilot_mdes.json`.
- [ ] **T032**: **State Update (Phase 1)**. Update `state.yaml` with hashes of `data/derived/` and `results/`.

### Phase 2: Core Modeling (Consolidated with T011c)
- [ ] **T012**: **Model Fitting Verification**.
  - (Note: Primary fitting logic moved to T011c for artifact flow).
  - Verify convergence of the LMM fitted in T011c.
  - Extract fixed effects, random effects variance, and p-values.
  - Output: `results/lmm_final_summary.json` (validated against `contracts/drift_model_output.schema.yaml`).

### Phase 3: Robustness & Aggregation
- [ ] **T020**: **Permutation Test (Year)**.
  - Shuffle `year` labels [deferred] times. Refit the LMM (`power_residual ~ year`).
  - Compare observed slope to null distribution.
  - Output: `results/permutation_pvalue.json` (validated against `contracts/permutation_result.schema.yaml`).
- [ ] **T021**: **Sensitivity Analysis**.
  - Read `results/lmm_final_summary.json`.
  - Sweep alpha across a range of values..
  - Output: `results/sensitivity_report.json` (validated against `contracts/sensitivity_report.schema.yaml`).
- [ ] **T025**: **Field-Specific Stratification**.
  - Fit LMM separately for each `field` using `power_residual ~ year`.
  - Output: `results/field_slopes.csv` (validated against `contracts/field_slopes.schema.yaml`).
- [ ] **T026**: **Cross-Field Aggregation**.
  - Read `results/field_slopes.csv`.
  - Apply DerSimonian-Laird to combine slopes.
  - Output: `results/aggregated_drift.json` (validated against `contracts/aggregated_drift.schema.yaml`).
- [ ] **T027**: **Input Permutation Framework**.
  - Read `data/derived/cleaned_data.csv`.
  - Shuffle `effect_size` and `sample_size` (holding `year` constant) to generate a null distribution of slopes.
  - Compare observed slope to this distribution.
  - Output: `results/input_permutation_summary.json` (validated against `contracts/permutation_result.schema.yaml`).
- [ ] **T028**: **Non-Linearity Check**.
  - Fit model with `ns(year, df=3)`. Compare AIC to linear model.
  - Output: `results/nonlinearity_check.json`.
- [ ] **T032**: **State Update (Phase 3)**. Update `state.yaml` with hashes of all robustness outputs.

### Phase 4: Visualization & Reporting
- [ ] **T013**: **Visualization**.
  - Read `data/derived/residuals.csv` and `results/lmm_final_summary.json`.
  - Generate scatter plot of `power_residual` vs. `year` with fitted line and confidence interval.
  - Output: `results/power_drift_plot.png`.
- [ ] **T032**: **State Update (Phase 4)**. Update `state.yaml` with hash of `results/power_drift_plot.png`.

## Testing Strategy

- **Unit Tests**: Validate power calculation formulas, MDES logic, and schema validation.
- **Integration Tests**: Verify data flow from `data/raw` to `results/`.
- **Schema Validation**: All JSON/CSV outputs (`lmm_final_summary.json`, `field_slopes.csv`, `input_permutation_summary.json`, etc.) are validated against their respective schemas in `contracts/` before being accepted as final outputs.
- **Reproducibility**: Run pipeline on a fresh runner; verify `state.yaml` hashes match.
