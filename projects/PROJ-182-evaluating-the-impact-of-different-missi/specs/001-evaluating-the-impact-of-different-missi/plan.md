# Implementation Plan: Evaluating the Impact of Different Missing Data Mechanisms on Regression Discontinuity Designs

**Branch**: `001-evaluating-missing-data-rd` | **Date**: 2026-06-24 | **Spec**: `specs/001-evaluating-the-impact-of-different-missi/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-different-missi/spec.md`

## Summary

This feature implements a Monte-Carlo simulation study to evaluate the robustness of Regression Discontinuity (RD) designs under three missing data mechanisms: Missing Completely At Random (MCAR), Missing At Random (MAR), and Missing Not At Random (MNAR). The system generates synthetic RD datasets with known ground truth, applies controlled missingness, and compares four estimation strategies: Naïve Local-Linear, Multiple Imputation (MI), Inverse-Probability Weighting (IPW), and a Selection-Model (Heckman-type) correction. The plan ensures strict adherence to the project constitution regarding reproducibility, data hygiene, and computational feasibility on CPU-only CI.

**Critical Methodological Updates**:
1.  **Heckman Identification**: The data generation process now explicitly includes an **exclusion restriction** (a covariate $Z^*$ that affects missingness but not the outcome) to ensure the Heckman model is identified.
2.  **Naïve Baseline**: The Naïve estimator is defined as **listwise deletion** (complete-case analysis), which is expected to be biased under MNAR.
3.  **IPW Blindness**: The IPW estimator is strictly constrained to use **only observed data** for propensity score estimation, ensuring its failure under MNAR is a statistical property, not a coding artifact.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `pyyaml`  
**Storage**: Local file system (`data/`, `results/`); No external database.  
**Testing**: `pytest` (unit tests for data generation logic; integration tests for pipeline flow).  
**Target Platform**: GitHub Actions Free Tier (Linux, multiple CPU, ~7GB RAM, no GPU).  
**Project Type**: Computational Research Simulation  
**Performance Goals**: Complete 36 configuration sets (mechanisms × 3 rates × 4 estimators) within 6 hours on CPU.  
**Constraints**: No GPU usage; memory usage < 6GB; no external real-world datasets required (synthetic data only).  
**Scale/Scope**: A substantial number of Monte-Carlo replications per configuration; synthetic data generation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy | Status |
| :--- | :--- | :--- |
| **I. Reproducibility** | All random seeds pinned in `config/simulation.yaml`; `requirements.txt` pins exact versions. Scripts run end-to-end without manual intervention. | ✅ |
| **II. Verified Accuracy** | Citations in `research.md` limited to verified URLs or standard statistical literature (Imbens & Kalyanaraman, Rubin). **The Reference-Validator Agent must be invoked on `research.md` citations as a blocking gate before the simulation pipeline runs.** | ✅ |
| **III. Data Hygiene** | Synthetic data generated on-the-fly; intermediate results checksummed in `state/`. No PII (synthetic only). | ✅ |
| **IV. Single Source of Truth** | All metrics (Bias, RMSE, Coverage) trace to `results/metrics.csv`. Paper figures generated directly from this file. | ✅ |
| **V. Versioning Discipline** | **Every artifact under this project carries a content hash.** The `state` YAML file is updated on **any** artifact change (not just completion) to reflect the current versioning discipline. | ✅ |
| **VI. Missingness Protocol** | Mechanisms (MCAR/MAR/MNAR) strictly implemented per spec; seeds and rates logged in `config/missingness.yaml`. | ✅ |
| **VII. Simulation & Estimator Transparency** | Estimators (Naïve, MI, IPW, Heckman) encapsulated in `code/estimators/`. Parameters in `config/estimation.yaml`. **Outputs are validated against contract schemas (`contracts/*.schema.yaml`) during execution.** | ✅ |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-impact-of-different-missi/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── simulation_config.schema.yaml
    ├── estimation_result.schema.yaml
    └── aggregated_metric.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config/
│   ├── simulation.yaml      # Seeds, sample size, true effect
│   ├── missingness.yaml     # Rates, mechanisms, variable targets
│   └── estimation.yaml      # Bandwidth rules, imputation count
├── data/
│   └── .gitkeep             # Generated data stored here (not committed)
├── src/
│   ├── generators/
│   │   ├── rd_data.py       # Synthetic RD data generation (includes exclusion restriction Z*)
│   │   └── missingness.py   # MCAR, MAR, MNAR mask generation
│   ├── estimators/
│   │   ├── naive_rd.py      # Local-linear with IK bandwidth (listwise deletion)
│   │   ├── multiple_imputation.py # MICE logic
│   │   ├── ipw.py           # Inverse Probability Weighting (observed data only)
│   │   └── selection_model.py     # Heckman-type correction (requires Z*)
│   ├── metrics/
│   │   └── aggregation.py   # Bias, RMSE, Coverage calculation
│   └── viz/
│       └── heatmaps.py      # Result visualization
├── tests/
│   ├── unit/
│   │   └── test_missingness.py
│   └── integration/
│       └── test_pipeline.py
└── main.py                  # Orchestration script (validates outputs against contracts)

data/
└── .gitkeep

results/
└── .gitkeep
```

**Structure Decision**: Selected a modular `src/` structure to separate data generation, estimation, and aggregation logic. This supports unit testing of individual estimators and ensures the main pipeline is clean. No external database is used; data is stored as CSV/Parquet in `data/` and `results/`. **The main pipeline explicitly validates all intermediate and final outputs against the schema files defined in `contracts/`**.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Heckman Selection Model** | Required by FR-008 to address MNAR bias theoretically. | Simpler MNAR corrections (e.g., pattern mixture) lack the joint modeling capability required to test the specific "selection bias" hypothesis in RD. **Requires exclusion restriction Z* for identification.** |
| **Replications** | Required by FR-006 for stable metric estimation. | Fewer replications (e.g., 100) would yield high variance in Bias/RMSE estimates, obscuring the comparison between mechanisms. |
| **Multiple Estimators** | Required to compare robustness (Naïve vs. MI vs. IPW vs. Selection). | A single estimator would not demonstrate the *impact* of missingness mechanisms or the efficacy of corrections. |
| **Exclusion Restriction (Z*)** | Required to identify the Heckman model. | Without Z*, the Heckman model is unidentified, rendering the comparison scientifically invalid. |
| **IPW Blindness Constraint** | Required to ensure valid failure mode demonstration. | If IPW uses ground truth Y, the "failure" under MNAR becomes a coding error rather than a statistical property. |


## Contract Validation Strategy

The simulation pipeline will validate all generated data and results against the following contract schemas located in `contracts/`:
- `simulation_config.schema.yaml`: Validates configuration parameters before simulation starts.
- `estimation_result.schema.yaml`: Validates output of each replication.
- `aggregated_metric.schema.yaml`: Validates final aggregated metrics.

This ensures data integrity and compliance with the project's single source of truth principle.