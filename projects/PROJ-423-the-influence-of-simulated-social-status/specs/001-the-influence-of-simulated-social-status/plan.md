# Implementation Plan: Simulated Social Status & Risk-Taking

**Branch**: `001-simulated-status-risk` | **Date**: 2026-07-14 | **Spec**: `specs/001-simulated-status-risk/spec.md`
**Input**: Feature specification from `/specs/001-simulated-status-risk/spec.md`

## Summary

This project investigates the *statistical sensitivity* of an experimental design intended to test the causal influence of observing simulated social status (High vs. Low) and observed behavior (Risky vs. Conservative) on an individual's subsequent risk-taking. Due to the unavailability of a single public dataset with a fully crossed factorial design (Status × Behavior), the implementation will **simulate a synthetic dataset** based on *hypothesized* meta-analytic effect sizes. 

**Crucial Distinction**: The simulation is designed to **validate the analysis pipeline** and **determine statistical power**, NOT to empirically validate the psychological hypothesis itself. A significant result in this simulation confirms that the *method* can detect the effect if it exists, but does not prove the effect exists in reality. The primary goal is to ensure that if real data were collected with this design, the analysis would be capable of detecting the hypothesized interaction.

The analysis will employ **Ordinary Least Squares (OLS) / Fixed-Effects ANOVA** for the default between-subjects design (with Mixed-Effects Models reserved only for detected within-subjects structures). The entire pipeline is designed to run on a GitHub Actions CPU-only runner using `scikit-learn`, `statsmodels`, and `pandas`.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `pyyaml`
**Storage**: Local filesystem (`data/raw/`, `data/processed/`) for CSV/JSON artifacts.
**Testing**: `pytest` with `contract` tests validating schema compliance.
**Target Platform**: Linux (GitHub Actions Free Tier: 2 vCPU, ~7GB RAM).
**Project Type**: Computational Research / Data Analysis Pipeline / Power Analysis.
**Performance Goals**: Complete power analysis, data simulation, cleaning, modeling, and reporting within 6 hours. Memory usage < 6GB.
**Constraints**: No GPU available; must use CPU-optimized statistical methods. No access to gated clinical data.
**Scale/Scope**: Simulated dataset of [N calculated via Power Analysis] participants.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `code/` will contain `requirements.txt` with pinned versions. `random_seed` will be hardcoded in simulation scripts. |
| **II. Verified Accuracy** | **PASS** | Effect sizes for simulation will be derived from meta-analyses. **Mechanism**: The Reference-Validator Agent will verify all cited meta-analyses against primary sources before the simulation parameters are set in `code/config.py`. |
| **III. Data Hygiene** | **PASS** | `data/raw/` will store the raw simulation output (checksummed). `data/processed/` will store derived CSVs. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final report will be generated programmatically from `data/processed/`. **`structure_config.json` is generated dynamically** by `code/analysis.py` by inspecting the actual `participant_id` counts in the processed CSV, ensuring the config reflects the data reality, not hardcoded assumptions. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes will be recorded in `state/` upon completion of each phase. |
| **VI. Experimental Condition Integrity** | **PASS** | Simulation logic will enforce random assignment of `status_level` and `observed_behavior` to ensure orthogonality. |
| **VII. Standardized Risk Metric** | **PASS** | The simulated `risk_taking_score` will be derived from a parameterized distribution mimicking the Balloon Analog Risk Task (BART), as documented in the simulation config. |

## Project Structure

### Documentation (this feature)

```text
specs/001-simulated-status-risk/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Schema definitions)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Simulation parameters, seeds, paths
├── power_analysis.py    # NEW: Calculates N required for 80% power
├── simulate.py          # Data generation logic (FR-001)
├── preprocess.py        # Cleaning, binning, imputation (FR-002)
├── analysis.py          # Model selection (OLS vs LMM), VIF, sensitivity (FR-003, FR-004, FR-005)
├── report.py            # Plotting (Forest plot), summary generation (FR-007)
└── utils.py             # Helper functions

data/
├── raw/                 # Raw simulation output (checksummed)
└── processed/           # Cleaned CSVs, structure_config.json (dynamically generated)

tests/
├── __init__.py
├── conftest.py          # Fixtures for test data
├── unit/                # Unit tests for logic
└── contract/            # Schema validation tests (test_model_output.py)

contracts/               # Schema definitions used by tests
├── data.schema.yaml
└── model_output.schema.yaml

requirements.txt
.gitignore
```

**Structure Decision**: Single project structure selected to minimize overhead. The `code/` directory contains the entire pipeline from simulation to reporting. `tests/contract` validates the output schemas defined in `contracts/`.

## Contract Mapping

The `tests/contract/` directory contains test files that explicitly validate against the schemas in the `contracts/` directory:
- `tests/contract/test_data_schema.py` validates `data/processed/cleaned_data.csv` against `contracts/data.schema.yaml`.
- `tests/contract/test_model_output.py` validates `data/processed/structure_config.json` against `contracts/model_output.schema.yaml`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Power Analysis Phase | Required to determine N before simulation to ensure adequate power (Addressing Methodology Concern). | Arbitrary N selection risks underpowered or overpowered studies, invalidating statistical conclusions. |
| OLS vs LMM Selection | Required to match the model to the data structure (Between vs Within). | Applying LMM to between-subjects data causes singular fit errors; applying OLS to within-subjects data ignores clustering. |
| Sensitivity Sweep (, 3.0, 3.5 SD) | Required by FR-005 to validate robustness of outlier handling. | Single-threshold analysis risks false positives if the outlier definition is arbitrary. |
| Synthetic Data Generation | No single public dataset exists with the required factorial design. | Using a real dataset with missing variables would violate causal assumptions. |

## Phase Plan

### Phase 0: Power Analysis & Verification
1. **Verify Citations**: Reference-Validator Agent verifies meta-analytic sources for effect sizes.
2. **Calculate N**: Run `power_analysis.py` to determine the minimum N required to detect the hypothesized interaction with adequate statistical power (standard alpha level).
3. **Update Config**: Write the calculated N to `code/config.py`.

### Phase 1: Data Simulation & Preprocessing
1. **Simulate**: Run `simulate.py` to generate `data/raw/simulation_output.csv` with N participants.
2. **Preprocess**: Run `preprocess.py` to clean data, handle missing values, and bin variables. Output `data/processed/cleaned_data.csv`.
3. **Detect Design**: `preprocess.py` checks if `participant_id` has multiple rows to determine if the design is "between-subjects" or "within-subjects".

### Phase 2: Analysis
1. **Dynamic Model Selection**: `analysis.py` reads `data/processed/cleaned_data.csv`.
   - If **Between-Subjects**: Fit OLS/ANOVA (`risk_taking ~ status_level * observed_behavior`).
   - If **Within-Subjects**: Fit LMM (`risk_taking ~ status_level * observed_behavior + (1|participant_id)`).
2. **Generate Config**: `analysis.py` dynamically computes `type` and `n_subjects` from the data and writes `data/processed/structure_config.json`.
3. **VIF & Sensitivity**: Calculate VIF and run sensitivity sweep (, 3.0, 3.5 SD).

### Phase 3: Reporting
1. **Plot**: Generate forest plot and sensitivity tables.
2. **Report**: Generate final HTML/PDF summary.
3. **Verify**: Run `pytest` to ensure all contracts are met.