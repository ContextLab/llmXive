# Implementation Plan: The Influence of Simulated Social Status on Risk-Taking Behavior

**Branch**: `001-simulated-status-risk` | **Date**: 2026-07-13 | **Spec**: `specs/001-simulated-status-risk/spec.md`
**Input**: Feature specification from `specs/001-simulated-status-risk/spec.md`

## Summary

This project implements a rigorous statistical analysis pipeline to test the hypothesis that observing higher-status agents engaging in risky behavior increases an individual's subsequent risk-taking, and observing lower-status agents decreases it. Due to the infeasibility of finding a single public dataset with a fully crossed factorial design (Status × Behavior), the project adheres to **FR-001** by generating a synthetic dataset based on a simulated *observational learning process* (Option A) or aggregating separate trials (Option B).

**Critical Methodological Clarification**: The synthetic data generation is framed as a **"Recovery Test"** and **"Mechanism Validation"** rather than a discovery of new real-world effects. The simulation models the *process* of observation (agents observing status cues and updating risk parameters via a probabilistic learning rule), ensuring the causal mechanism is explicit. The analysis tests whether the statistical pipeline can correctly recover the known interaction effect embedded in the simulation (Power/Recovery) and can correctly identify a null effect in a "Null Simulation" mode (Type I error control). This distinguishes the work from a tautological "mean-shifting" simulation.

The pipeline includes:
1.  **Data Generation**: Simulates an observational learning process (BART-based) with orthogonal assignment of status and behavior.
2.  **Preprocessing**: Cleans data, detects outcome type (continuous/binary), and detects design type (within/between-subjects).
3.  **Adaptive Analysis**: Fits mixed-effects models (with or without random effects) based on detected design, calculates VIF, and performs sensitivity sweeps.
4.  **Reporting**: Generates forest plots, CI widths, Bonferroni-corrected p-values, and stability metrics.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, `pyyaml`, `pytest`  
**Storage**: Local files (`data/raw/`, `data/processed/`, `code/`)  
**Testing**: `pytest` (unit tests for data generation, integration tests for model fitting). **Configuration**: `pytest.ini` at `code/` with coverage goal >80%.  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, ~7 GB RAM)  
**Project Type**: Computational Research / Statistical Analysis  
**Performance Goals**: Complete full analysis (simulation, model fitting, sensitivity sweep) within 6 hours on CPU.  
**Constraints**: No GPU required (CPU-tractable statistical methods); memory usage < 7 GB; strict adherence to reproducibility (random seeds).  
**Scale/Scope**: Simulation of a large cohort of synthetic participants (power-justified); multiple experimental conditions; 3 sensitivity thresholds.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Reference / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`; `requirements.txt` at `code/`; data fetched/generated programmatically. |
| **II. Verified Accuracy** | **PASS** | All citations validated by **Reference-Validator Agent**; `CITATION_TITLE_OVERLAP_THRESHOLD` = 0.7 enforced. |
| **III. Data Hygiene** | **PASS** | Raw data (simulated) checksummed; derivations written to new files; no PII in synthetic data. |
| **IV. Single Source of Truth** | **PASS** | All statistics in reports trace to `data/processed/` and `code/`; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | **Action**: `code/hash_update.py` computes content hashes for all artifacts and updates `state/projects/PROJ-423-...yaml` on every run. |
| **VI. Experimental Condition Integrity** | **PASS** | Simulation enforces orthogonal assignment via explicit observation process; no leakage. |
| **VII. Standardized Risk Metric** | **PASS** | Simulation uses **Balloon Analog Risk Task (BART)** parameters; `data/processed/simulation_parameters.json` records instrument source. |

## Project Structure

### Documentation (this feature)

```text
specs/001-simulated-status-risk/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (Generated in subsequent 'Tasking' stage, NOT here)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, hyperparameters
├── generate_data.py     # Synthetic data generation (FR-001, BART-based observation process)
├── preprocess.py        # Cleaning, binning, outcome/design detection (FR-002, FR-003)
├── analysis.py          # Mixed-effects model, VIF, sensitivity sweep (FR-003, FR-004, FR-005)
├── reporting.py         # Forest plots, PDF/HTML generation (FR-007)
├── hash_update.py       # Computes hashes and updates state file (Constitution Principle V)
└── tests/
    ├── test_data_gen.py
    ├── test_preprocess.py
    └── test_analysis.py

data/
├── raw/                 # (Empty or meta-analysis registry if used)
└── processed/
    ├── cleaned_data.csv
    ├── outcome_type.json
    ├── design_type.json
    ├── simulation_parameters.json  # Records BART params, effect sizes, seed (SC-004)
    ├── model_config.json
    ├── model_results.json          # Includes ci_width, vif_scores, adjusted_p_values
    ├── sensitivity_results.json
    └── stability_metric.json       # Validates SC-002
```

**Structure Decision**: Single-project structure selected for a linear research pipeline. Data flows from `generate_data` -> `preprocess` -> `analysis` -> `reporting`. All artifacts are stored in `data/processed/` with explicit JSON schemas defined in `contracts/`.

## Implementation Phases (High-Level Flow)

1.  **Phase 0: Data Generation & Preprocessing**
    *   Generate synthetic data via `generate_data.py` (BART-based observation process).
    *   Run `preprocess.py` to clean data, detect `outcome_type` (continuous/binary), and detect `design_type` (within/between).
    *   Write `cleaned_data.csv`, `outcome_type.json`, `design_type.json`, `simulation_parameters.json`.
2.  **Phase 1: Model Configuration & Fitting**
    *   Run `analysis.py` to read config, detect design, and fit adaptive model (Mixed-Effects if within-subjects, OLS/GLM if between).
    *   Calculate VIFs.
    *   Write `model_config.json`, `model_results.json` (including `ci_width`, `vif_scores`).
3.  **Phase 2: Sensitivity & Validation**
    *   Run sensitivity sweep (varying SD values).
    *   Calculate Bonferroni-adjusted p-values for post-hoc comparisons.
    *   Validate stability (SC-002) and write `stability_metric.json`.
4.  **Phase 3: Reporting**
    *   Generate forest plot and final report.
    *   Run `hash_update.py` to update state file.

## Complexity Tracking

No violations detected. The synthetic data approach is explicitly framed as a "Recovery Test" for mechanism validation, avoiding tautology by including "Null Simulation" modes and distinguishing between simulation validation and real-world discovery.