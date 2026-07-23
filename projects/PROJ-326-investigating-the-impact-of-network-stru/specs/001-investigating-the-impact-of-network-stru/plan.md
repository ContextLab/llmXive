# Implementation Plan: Network Topology Energy Transfer in Spin Systems

**Branch**: `001-network-topology-energy-transfer` | **Date**: 2025-01-15 | **Spec**: `specs/001-network-topology-energy-transfer/spec.md`
**Input**: Feature specification from `/specs/001-network-topology-energy-transfer/spec.md`

## Summary

This feature implements a computational physics pipeline to investigate the impact of network structure on energy transfer in spin systems. The system generates synthetic spin networks (Erdős-Rényi, Scale-Free, Small-World) using a **stratified generation strategy** to decouple topological metrics, runs a simplified non-equilibrium Ising spin-flip dynamics simulator on CPU, measures energy diffusion rates (rate of change of spatial variance), and performs statistical regression/ANOVA with **Ridge Regression** and **Partial Correlation** to isolate metric effects. The plan strictly adheres to CPU-only constraints (≤7GB RAM, 2 cores) and ensures all data artifacts are checksummed, schema-validated, and reproducible via pinned random seeds.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx>=3.2`, `numpy>=1.26`, `scipy>=1.12`, `pandas>=2.1`, `matplotlib>=3.8`, `seaborn>=0.13`, `pyyaml>=6.0`, `statsmodels>=0.14`  
**Storage**: Local file system (`data/raw`, `data/analysis`); JSON/CSV for structured data, PNG for figures.  
**Testing**: `pytest>=7.4`, `hypothesis` (for property-based graph generation tests).  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 vCPU, ~7GB RAM, no GPU).  
**Project Type**: Computational research library / CLI pipeline.  
**Performance Goals**: 
- Generate 100+ valid connected graphs within 30 mins.
- Simulate 100 steps on 500-node graph within 60 mins (SC-002).
- Total pipeline execution < 6 hours (dynamic allocation based on pilot variance).  
**Constraints**: 
- No external data downloads (synthetic only).
- No GPU acceleration.
- Memory < 7GB (streaming or batch processing of small graphs).
- Strict adherence to schema contracts for all JSON outputs.  
**Scale/Scope**: 
- Batch size: A moderate range of graphs per run (stratified by clustering bins).
- Network size: variable scale.
- Time steps: a fixed number of steps per simulation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action Plan |
|-----------|--------|------------------------|
| **I. Reproducibility** | **PASS** | `requirements.txt` will pin all versions. `config.yaml` will store all random seeds. `code/` scripts will be runnable end-to-end. |
| **II. Verified Accuracy** | **PASS** | Task T000: Run Reference-Validator Agent on all citations. Output artifact `state/citations_verified.json` will be generated. `main.py` will fail if this file is missing or contains errors. |
| **III. Data Hygiene** | **PASS** | All generated data files (`data/raw/*.json`, `data/analysis/*.json`) will be checksummed (SHA-256) in `state/`. No in-place modification; derivations produce new files. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` will be parsed directly from `data/analysis/aggregated_results.json` via a script, preventing hand-typing. |
| **V. Versioning Discipline** | **PASS** | Content hashes for `code/` and `data/` will be recorded in `state/...yaml` upon every artifact write. |
| **VI. Synthetic Data Transparency** | **PASS** | Every graph batch will generate a `metadata.json` in `data/raw` containing algorithm, parameters, and seed. |
| **VII. Statistical Integrity** | **PASS** | All statistical tests (regression, ANOVA) will output full pipelines (test type, alpha, correction method) to `data/analysis/statistical_report.json`. Ridge regression and partial correlation outputs included. |

## Project Structure

### Documentation (this feature)

```text
specs/001-network-topology-energy-transfer/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Loads config.yaml, manages seeds
├── generators/
│   ├── __init__.py
│   ├── network_generator.py  # ER, SF, WS generation with stratified sampling
│   └── batch_manager.py      # Handles global batch, retry logic
├── simulation/
│   ├── __init__.py
│   ├── ising_model.py        # Spin-flip dynamics, energy density calc
│   └── diffusion_metrics.py  # Spatial variance, diffusion rate (FR-003)
├── analysis/
│   ├── __init__.py
│   ├── regression.py         # Linear/non-linear, ANOVA, Ridge, Partial Correlation
│   ├── sensitivity.py        # Threshold sweep (FR-008)
│   └── power_analysis.py     # SC-003 calculation
├── io/
│   ├── __init__.py
│   ├── serializer.py         # Writes JSON/CSV with schema validation
│   └── validator.py          # Validates against contracts
├── main.py                  # Orchestrator: Gen -> Sim -> Analyze -> Report
└── requirements.txt

data/
├── raw/
│   ├── global_batch_manifest.json
│   └── metadata.json
├── analysis/
│   ├── simulation_results.json
│   ├── sensitivity_sweep.json
│   ├── aggregated_results.json
│   ├── statistical_report.json
│   ├── power_analysis_report.json
│   └── final_results.json
└── figures/
    └── *.png

tests/
├── unit/
│   ├── test_generators.py
│   ├── test_simulation.py
│   └── test_metrics.py
├── contract/
│   └── test_schemas.py       # Validates JSON against contracts/*.yaml
└── integration/
    └── test_pipeline.py
```

**Structure Decision**: Single project structure (Option 1) chosen. The domain is a linear pipeline (Generate -> Simulate -> Analyze) with no need for separate frontend/backend or mobile components. This minimizes overhead and fits the computational research scope.

## Complexity Tracking

> **No violations detected.** The plan adheres strictly to the spec and constitution.

## Task Definitions Added (Previously Unresolved Panel Concerns)

*Note: These tasks are defined for implementation in Phase 2. The code artifacts are pending creation.*

1.  **T000 (Citation Validation)**: Implement `run_reference_validator` in `main.py`. Generates `state/citations_verified.json`. Fails pipeline if validation fails.
2.  **T002 (Pilot Variance Estimation)**: Run a small batch (N=20) to estimate variance. If power < 0.8, increase batch size up to 6-hour limit. Report limitation if limit reached.
3.  **T029 (Result Serialization)**: Implement `diffusion_metrics.py` to calculate `diffusion_rate` as rate of change of spatial variance (FR-003).
4.  **T029a (Schema Validation)**: Validate `data/analysis/simulation_results.json` against `contracts/simulation_results.schema.yaml` including `runtime_duration_seconds` and `generation_algorithm`.
5.  **T035b (Sensitivity Sweep Validation)**: Implement `sensitivity.py` to generate `data/analysis/sensitivity_sweep.json`. Validate that `thresholds_tested` has ≥5 distinct values.
6.  **T037a (Aggregation)**: Implement `aggregate_results.py` to write `data/analysis/aggregated_results.json` including Ridge and Partial Correlation results.
7.  **T037d (Final Serialization)**: Implement `serialize_final.py` to write `data/analysis/final_results.json` (no `timestamp` field).
8.  **T044 (Power Analysis)**: Implement `power_analysis.py` to write `data/analysis/power_analysis_report.json`.
9.  **T045a (Validation)**: Implement `validate_batch.py` to extract `generation_algorithm` and `parameter_values` from `simulation_results.json`.
10. **T055 (Runtime Validation)**: Implement `validate_sc_002` in `validate_batch.py` to check `runtime_duration_seconds` ≤ 3600s.

## Phases

### Phase 0: Research & Data Strategy
*   **Goal**: Confirm algorithmic feasibility on CPU, define statistical rigor, and validate citations.
*   **Tasks**: 
    *   **T000**: Run Reference-Validator Agent on all citations (Watts & Strogatz, Cohen, Glauber). Generate `state/citations_verified.json`.
    *   **T002**: Run Pilot Variance Estimation (N=20). Estimate effect size variance. Determine if batch size needs adjustment within 6h limit.
    *   Verify `networkx` Watts-Strogatz generation meets clustering targets (SC-001) with stratified sampling.
    *   Profile `numpy`-based Ising simulation for 500 nodes/100 steps to ensure <60 min runtime (SC-002).
    *   Define power analysis parameters for 100+ realizations (SC-003).
*   **Output**: `research.md`, `state/citations_verified.json`.

### Phase 1: Data Model & Contracts
*   **Goal**: Define strict schemas for all data artifacts to prevent schema drift.
*   **Tasks**: 
    *   Define `SimulationRun`, `NetworkGraph`, `AnalysisResult` schemas in YAML.
    *   Create validation logic.
    *   Ensure `contracts/sensitivity_sweep.schema.yaml` enforces a minimum number of items to ensure diversity and uniqueness (`uniqueItems: true`).
*   **Output**: `data-model.md`, `contracts/*.schema.yaml`.

### Phase 2: Implementation (Orchestrated by Implementer Agent)
*   **Goal**: Build the pipeline.
*   **Tasks**: 
    *   **T029**: Implement `generators/` with **stratified sampling** by clustering coefficient bins (0.1, 0.2, 0.3, 0.4, 0.5) to ensure coverage for SC-005.
    *   **T029**: Implement `simulation/` with divergence detection.
    *   **T029**: Implement `diffusion_metrics.py` to calculate `diffusion_rate` as rate of change of spatial variance (FR-003).
    *   **T035b**: Implement `analysis/sensitivity.py` with validation for ≥5 distinct thresholds.
    *   **T037a**: Implement `analysis/regression.py` with **Ridge Regression** and **Partial Correlation** to handle collinearity.
    *   **T029a/T045a/T055**: Implement `io/validator.py` and `tests/contract/` to validate schemas and runtime constraints.
    *   Implement `io/` for schema-validated JSON writing.
*   **Output**: `code/`, `data/`.

### Phase 3: Verification & Reporting
*   **Goal**: Run full pipeline, validate outputs, generate figures.
*   **Tasks**: 
    *   Execute `main.py`.
    *   Run `tests/contract/` and `tests/unit/`.
    *   **T055**: Run `validate_sc_002` to verify SC-002 compliance.
    *   Generate `final_results.json` and figures.
*   **Output**: `data/analysis/final_results.json`, `data/figures/*.png`.