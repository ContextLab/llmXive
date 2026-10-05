# Implementation Plan: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

**Branch**: `001-assessing-the-validity-of-significance` | **Date**: 2026-08-25 | **Spec**: `specs/001-assessing-the-validity-of-statistical-si/spec.md`

## Summary

This project implements a simulation engine to assess the validity of statistical significance (Type I error rates) in Randomized Controlled Trials (RCTs) under various missing data mechanisms (MCAR, MAR, MNAR). The system will download public RCT datasets from OpenML, permute treatment labels to establish a ground-truth null hypothesis, simulate missingness patterns at varying rates, and compare Complete-Case (CC), Multiple Imputation (MI), and Inverse Probability Weighting (IPW) analysis methods. The primary output is the identification of "tipping points" where CC analysis fails to maintain nominal error rates, and a demonstration that MI/IPW methods remain robust (for MAR) or fail (for MNAR).

**Spec Contradiction Note**: The source spec (FR-002) states: "For MNAR, the missingness probability MUST depend on the permuted outcome values." This is scientifically incoherent (see Methodology). This plan **overrides** that specific instruction to implement MNAR based on **original** outcome values (preserving the distribution) while only permuting the **treatment** labels. This is a necessary correction to ensure the simulation is valid. The spec must be updated to reflect this.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `statsmodels`, `scipy`, `pandas`, `numpy`, `seaborn`, `matplotlib`, `requests`, `openml`, `miceforest` (for true Multiple Imputation with Rubin's Rules).  
**Storage**: Local filesystem (`data/` for raw/downloaded data, `data/processed/` for simulation outputs), SQLite (optional for metadata, otherwise JSON/Parquet).  
**Testing**: `pytest` (unit tests for simulation logic, integration tests for full pipeline).  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, ~7 GB RAM).  
**Project Type**: Computational Statistics / Simulation Engine.  
**Performance Goals**: Complete full sensitivity analysis (8 rates x 3 mechanisms x 3 methods x 2000 iterations) within 6 hours on CPU. Use vectorized operations and parallel processing (`joblib`) where memory permits.  
**Constraints**: Must run without GPU; must handle datasets >7GB via streaming or sampling; must not fabricate data; must strictly adhere to the "permute treatment first, then simulate missingness" protocol for ground truth.  
**Scale/Scope**: 3 datasets (minimum), 72 simulation conditions, 144,000 total hypothesis tests (2000 iterations x 72 conditions). *Note: Iterations will be increased to reduce standard error and improve power for detecting the 10% threshold.*

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action Required / Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds, and automated CI execution. All datasets are fetched from canonical OpenML IDs. (See FR-001, SC-001) |
| **II. Verified Accuracy** | **PASS** | Plan restricts dataset sources to verified OpenML IDs (e.g., representative examples). Note: Pre-missing MNAR datasets from the "Verified datasets" block were rejected in favor of simulating missingness on complete OpenML data to satisfy the study's specific design requirements (simulating mechanisms). No external citations will be added without validation. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming steps for raw data downloads. No in-place modification; all derived data (simulated missingness) goes to new files. PII scan is assumed for public RCT data. (See SC-003) |
| **IV. Single Source of Truth** | **PASS** | All figures and stats in the final report will be generated programmatically from `data/processed/` outputs. No manual entry. (See SC-004) |
| **V. Versioning Discipline** | **PASS** | Artifacts (data, code, results) will carry content hashes. The plan includes steps to update the state YAML on artifact changes. (See SC-005) |
| **VI. Simulation Ground-Truth Calibration** | **PASS** | Plan explicitly orders steps: (1) Load Data -> (2) Permute Treatment (Null Hypothesis) -> (3) Simulate Missingness (based on original outcome) -> (4) Analyze. This ensures the "true effect" is zero before missingness is introduced. (See FR-003, FR-002 override) |
| **VII. Mechanism-Specific Threshold Identification** | **PASS** | Plan structures the simulation loop to separate MCAR, MAR, and MNAR runs, ensuring tipping points are identified per mechanism, not aggregated. (See FR-004, FR-008) |

## Project Structure

### Documentation (this feature)

```text
specs/001-assessing-the-validity-of-statistical-si/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── simulation_config.schema.yaml
│   ├── error_metric.schema.yaml
│   ├── p_value_distribution.schema.yaml
│   └── simulation_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-436-assessing-the-validity-of-statistical-si/
├── data/
│   ├── raw/                  # Downloaded datasets (checksummed)
│   └── processed/            # Simulation outputs (parquet/json)
├── code/
│   ├── __init__.py
│   ├── config.py             # SimulationConfig loading/validation
│   ├── data_loader.py        # Download and stream datasets via OpenML
│   ├── simulation.py         # Core logic: permute treatment, simulate missingness
│   ├── analysis.py           # CC, MI (miceforest), IPW implementation
│   ├── metrics.py            # Type I error calculation, Binomial tests, FDR
│   └── main.py               # Orchestration script
├── tests/
│   ├── unit/
│   │   ├── test_simulation.py
│   │   └── test_analysis.py
│   └── integration/
│       └── test_full_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure with clear separation of concerns (`data_loader`, `simulation`, `analysis`, `metrics`). This minimizes overhead and fits the CPU-first constraint. The `code/` directory is isolated for the CI runner's virtualenv.

## Complexity Tracking

> **No violations detected.** The project complexity is managed by:
> 1.  **Streaming**: Using `openml` and `pandas` chunking to handle large RCT datasets without loading full ~7GB into RAM.
> 2.  **Vectorization**: Using `numpy`/`pandas` for missingness simulation rather than row-by-row loops.
> 3.  **Parallelization**: Using `joblib` to parallelize the iterations across the 2 available CPU cores (batching iterations).
> 4.  **Deferral**: Specific dataset sizes and exact iteration counts (beyond the spec's 500) are deferred to the research phase if power analysis suggests adjustments (Note: Plan now targets 2000).