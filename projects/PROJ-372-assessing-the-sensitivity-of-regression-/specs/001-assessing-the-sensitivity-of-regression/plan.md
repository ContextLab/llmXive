# Implementation Plan: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

**Branch**: `PROJ-372-assessing-sensitivity-regression-coefficients` | **Date**: 2026-08-15 | **Spec**: [link]
**Input**: Feature specification from `specs/PROJ-372-assessing-sensitivity-regression-coefficients/spec.md`

## Summary

This project investigates the stability of OLS regression coefficients by systematically varying dataset subset sizes and analyzing the impact of OLS assumption violations (heteroscedasticity, outliers, multicollinearity). The technical approach involves ingesting verified numerical datasets from HuggingFace/UCI, profiling them for assumption violations, generating random subsets across five specific sample size tiers (**10, 25, 50, 75, 90** percentages of full size), fitting OLS models to each subset, and performing a **Hierarchical Linear Model (HLM)** to quantify the relationship between violation severity, subset size, and coefficient stability.

**Methodological Correction**: To address the "Dataset Identity" confound and the loss of within-tier variance, the analysis unit is shifted from aggregated "Tier-SD" values to **individual coefficient values** from each of the 1000 subsets (200 subsets $\times$ 5 tiers). The HLM treats "Dataset" as a Level 2 grouping factor. "Violation Severity" (computed on the full dataset) is a Level 2 predictor, while "Subset Size" is a Level 1 predictor. This allows the model to estimate how the *slope* of coefficient instability (change in coefficient value relative to subset size) varies by violation severity, without conflating dataset-specific noise with violation effects.

The implementation strictly adheres to the "Real Data Only" and "CPU-only" constraints, utilizing streaming for large datasets and pinned random seeds for reproducibility.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pyyaml`, `datasets` (HuggingFace), `pre-commit`, `pytest`, `matplotlib`, `seaborn`, `linearmodels` (for HLM)  
**Storage**: Local file system (`data/`, `artifacts/`) with JSON/Parquet artifacts; no external database.  
**Testing**: `pytest` (unit, integration, contract)  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM)  
**Project Type**: Computational Research / Data Analysis Pipeline  
**Performance Goals**: Complete full pipeline (ingestion -> resampling -> HLM) within 6 hours on CPU; memory usage < 7GB via streaming; standard error of SD < 5% convergence check (for data quality, not model input).  
**Constraints**: Real data only (no synthetic); CPU-only execution; streaming for datasets > 7GB; strict reproducibility (seeds pinned); no circular derivation of metrics.  
**Scale/Scope**: Process multiple datasets (verified sources); Multiple subsets per dataset; 5 tiers; HLM analysis.  
**Sample Size Tiers**: **10, 25, 50, 75, 90** (Percentages of full dataset size).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Plan Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/` (global `numpy.random.seed`, `random.seed`). External datasets fetched via canonical HuggingFace/UCI URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` restricted to verified URLs provided in the prompt. `Reference-Validator` logic embedded in CI checks. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw` with checksums recorded in `state/...yaml`. Derived data (subsets, profiles) in `data/processed` or `artifacts/`. No in-place modification. PII scan via `pre-commit`. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in report trace to `artifacts/` JSON/Parquet. No hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes. `state/...yaml` updated on artifact change. |
| **VI. Empirical Validation** | **PASS** | Plan explicitly maps coefficient stability (individual $\beta$ values) to **Breusch-Pagan (heteroscedasticity)**, **Cook's Distance (outliers)**, and **Condition Number (collinearity)**. **Methodology**: HLM models $\beta_{j, s}$ as a function of Subset Size (Level 1) and Violation Severity (Level 2), resolving the confound by using within-dataset variance for subset size effects and between-dataset variance for violation effects. |
| **VII. Non-Circular Derivation** | **PASS** | Stability metrics are derived from the HLM residuals or post-hoc aggregation of individual coefficients. Full-dataset violation metrics are calculated once on the full set; they are used as predictors, not as part of the outcome calculation. The HLM structure ensures the outcome (individual $\beta$) is independent of the predictor (full-dataset metric) except through the modeled relationship. |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-372-assessing-sensitivity-regression-coefficients/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (see Phase 1.1)
│   ├── aggregated_stability.schema.yaml
│   ├── dataset_profile.schema.yaml
│   ├── group_stability_comparison.schema.yaml
│   └── stability_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── ingestion/
│   ├── __init__.py
│   ├── loader.py          # Handles HuggingFace/UCI loading + streaming
│   └── profiler.py        # Computes Condition Number, BP, Cook's D + Severity Classification
├── resampling/
│   ├── __init__.py
│   ├── generator.py       # Generates Multiple subsets per tier
│   └── stability.py       # Fits OLS to each subset, stores individual coefficients
├── analysis/
│   ├── __init__.py
│   ├── hlm_analysis.py    # Fits Hierarchical Linear Model (Level 1: Subset, Level 2: Dataset)
│   └── viz.py             # Generates Stability Curves and HLM diagnostics
├── utils/
│   ├── __init__.py
│   ├── logging.py
│   └── config.py          # Seed management, constants
└── cli.py                 # Entry point

data/
├── raw/                   # Downloaded raw datasets (checksummed)
└── processed/             # Cleaned/filtered datasets

artifacts/
├── profiles/              # DatasetProfile JSONs
├── stability/             # stability_subset_*.json (individual coefficients per subset)
├── hlm_results/           # HLM model output JSON
├── convergence/           # convergence.log (T036, T050)
├── figures/               # Stability curves (US3 deliverable)
└── checkpoints/           # Intermediate state (if needed)

tests/
├── unit/
│   ├── __init__.py
│   └── test_profiler.py
├── integration/
│   ├── __init__.py
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py
```

**Structure Decision**: Selected Option 1 (Single project) with modular `src/` packages (`ingestion`, `resampling`, `analysis`, `utils`). This aligns with the computational research nature, keeping logic encapsulated and testable without unnecessary web/mobile abstractions.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Streaming Architecture** | Datasets > 7GB must be processed without OOM. | Loading full dataset into memory fails on GitHub Actions due to constrained memory limits. |
| **200 Subsets per Tier** | Required by spec to achieve convergence (SE < 5%) and provide sufficient Level 1 data points for HLM. | Fewer subsets (e.g., 50) would reduce the power of the HLM to detect the interaction effect. |
| **Hierarchical Linear Model (HLM)** | Spec requires analyzing joint effects of violation severity and subset size. | Simple regression or stratified comparison creates confounding (Dataset Identity vs. Violation Severity) or loses within-tier variance. HLM is the only valid approach to model the interaction between Level 1 (Subset Size) and Level 2 (Violation Severity) predictors. |
| **Convergence Enforcement** | Spec US2 requires verification of convergence. | Logging only is insufficient; a hard stop/flag is required to prevent proceeding with unstable results. |
| **Individual Coefficient Storage** | Required for HLM input. | Aggregating to SD per tier loses the variance needed for the Level 1 analysis. |

## Implementation Phases

### Phase 0: Data Ingestion & Profiling (US1)
- **0.1 Load**: Fetch datasets from verified URLs (UCI Bike Sharing, California Housing). Stream if >7GB.
- **0.2 Profile**: Compute Condition Number, Breusch-Pagan, Cook's Distance.
- **0.3 Classify**: **Explicitly assign severity levels (Low/Medium/High)** to each metric and write to `DatasetProfile` artifact. (US1 AC: "System classifies violation severity").
- **0.4 Validate**: Ensure `DatasetProfile` JSON matches `contracts/dataset_profile.schema.yaml`.

### Phase 1: Resampling & Stability Estimation (US2)
- **1.1 Generate**: Create Multiple random subsets for each of the 5 tiers (10, 25, 50, 75, 90).
- **1.2 Fit**: Fit OLS to each subset. Store **individual coefficients** for each predictor in `StabilityResult` JSONs (`artifacts/stability/stability_subset_*.json`).
- **1.3 Verify Convergence (GATE)**:
  - Calculate Empirical SD of coefficients across 200 subsets *per tier* (for data quality check).
  - Calculate Standard Error of the SD ($SE_{SD}$).
  - **Control Flow**: If $SE_{SD} \ge 0.05 \times SD$, **FLAG** the tier as "Convergence Failed" and **HALT** further analysis for this dataset. Write `convergence.log` (T036, T050).
  - **Note**: This check ensures the *stability metric* is reliable, but the HLM uses the raw individual coefficients regardless of the SD value.
- **1.4 Aggregate**: Generate `coefficient_sd.json` (T048) for descriptive reporting.

### Phase 2: Hierarchical Linear Modeling & Visualization (US3)
- **2.1 Prepare Data**: Combine individual `StabilityResult` rows (Level 1) with `DatasetProfile` (Level 2).
- **2.2 Fit HLM**:
  - **Model**: $\beta_{j, s} = \gamma_{00} + \gamma_{10}(\text{Size}_s) + \gamma_{01}(\text{Severity}_d) + \gamma_{11}(\text{Size}_s \times \text{Severity}_d) + u_{0d} + r_{js}$
  - **Level 1 (Subset)**: `Subset_Size`, `Coefficient_Value` (outcome).
  - **Level 2 (Dataset)**: `Violation_Severity`, `Condition_Number`.
  - **Output**: `hlm_results.json` (T049).
- **2.3 Visualize (US3 Deliverable)**: **Generate Stability Curves** (Predicted Coefficient Value vs. Subset Size) for different Severity groups based on HLM fixed effects. Save to `artifacts/figures/`.

## Tasks (Consolidated)

- [ ] **T001**: Create project directory structure (`src/`, `data/`, `artifacts/`, `tests/`) and all `__init__.py` files.
- [ ] **T002**: Create `requirements.txt` and `pre-commit-config.yaml`.
- [ ] **T003**: Implement `src/ingestion` (loader, profiler with severity classification).
- [ ] **T004**: Implement `src/resampling` (generator, stability with individual coefficient storage).
- [ ] **T005**: Implement `src/analysis` (hlm_analysis, viz for HLM curves).
- [ ] **T006**: Implement `tests/` (unit, integration, contract).
- [ ] **T007**: Run Pipeline (Ingest -> Profile -> Resample -> **Convergence Check** -> HLM -> **Generate Curves**).
- [ ] **T008**: Validate Artifacts (Schemas, Convergence Log, HLM Results, Stability Curves).

## Contract Definitions (Phase 1 Output)

The following schema files are defined in `contracts/` and will be used for validation:
1. `contracts/dataset_profile.schema.yaml`
2. `contracts/stability_result.schema.yaml` (Updated to store individual coefficients)
3. `contracts/aggregated_stability.schema.yaml`
4. `contracts/group_stability_comparison.schema.yaml` (Renamed to `hlm_results.schema.yaml` conceptually, but kept for compatibility or updated)

These contracts ensure data integrity across the pipeline.