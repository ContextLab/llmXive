# Implementation Plan: llmXive follow-up: extending "Infinite Worlds with Versatile Interactions"

**Branch**: `001-llmxive-followup` | **Date**: 2026-08-26 | **Spec**: `specs/001-llmxive-followup/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-followup/spec.md`

## Summary

This project implements a comparative simulation framework to evaluate a deterministic Cellular Automaton (CA) "Eco-Director" against a large-parameter neural proxy baseline. The primary goal is to determine if rule-based systems can achieve statistical parity in environmental coherence and diversity while meeting a ≥90% latency reduction target on CPU-only hardware. The approach involves a modular simulation engine, a systematic parameter sweep (neighborhood radius, memory depth, non-linearity), and rigorous statistical analysis (Linear Mixed-Effects Models, Random Forest) to isolate the drivers of emergent complexity. The simulation uses a "Stochastic Physics Sandbox" to inject external, uncontrolled environmental complexity, ensuring validity.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `statsmodels`, `huggingface_hub`, `torch` (CPU-only), `matplotlib`, `seaborn`, `pyyaml`  
**Storage**: Local CSV/Parquet files in `data/` (streamed/processed in memory chunks)  
**Testing**: `pytest` (unit tests for CA logic, integration tests for simulation pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM)  
**Project Type**: computational simulation / research library  
**Performance Goals**: ≤6h total job time, ≤7GB RAM peak, ≥90% latency reduction vs. neural baseline  
**Constraints**: No GPU access; strict memory ceiling; deterministic reproducibility (fixed seeds); Stochastic Physics Sandbox for external validity  
**Scale/Scope**: A sufficient number of time-steps per configuration (fractional factorial); Multiple noise seeds per config; Multiple simulation runs  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Compliance Status | Implementation Action |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | **COMPLIANT** | All random seeds pinned in `code/config.py`. External datasets (Sandbox) generated via deterministic pseudo-random generators with fixed seeds. |
| **II. Verified Accuracy** | **COMPLIANT** | Citations in `research.md` strictly limited to verified dataset URLs provided in the spec (none used; sandbox is self-contained). No unverified URLs introduced. |
| **III. Data Hygiene** | **COMPLIANT** | Raw data (simulation logs) preserved in `data/raw/`. Derived metrics in `data/processed/`. Checksums recorded in project state YAML. |
| **IV. Single Source of Truth** | **COMPLIANT** | All figures/stats in the final report will be generated via scripts reading `data/processed/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **COMPLIANT** | Artifacts will be versioned via content hashes. `state/` YAML updated on every change. |
| **VI. Deterministic Rule-Set Isolation** | **COMPLIANT** | CA engine (`code/sim/eco_director.py`) will strictly parameterize locality, memory, and non-linearity. Neural weights frozen and swapped via a strict interface. |
| **VII. Long-Horizon Statistical Parity Validation** | **COMPLIANT** | LMM will include 'noise_seed' as a random effect to account for stochastic variance. Partial Correlation Analysis implemented to ensure independence from input generation. Latency logged per step. ACF is computed for diagnostic reporting only, not as a model selection gate. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-followup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── simulation_run.schema.yaml
│   ├── metric_record.schema.yaml
│   └── physics_oracle.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── sim/
│   ├── __init__.py
│   ├── eco_director.py      # CA Engine (FR-001)
│   ├── neural_baseline.py   # 100M Parameter Proxy (FR-001)
│   └── physics_oracle.py    # Stochastic Physics Sandbox (FR-008)
├── analysis/
│   ├── __init__.py
│   ├── lmm_runner.py        # Linear Mixed-Effects Model (FR-004)
│   ├── rf_runner.py         # Random Forest Feature Importance (FR-009)
│   ├── acf_validator.py     # Autocorrelation Check (FR-007 - Diagnostic Only)
│   └── sensitivity.py       # Sensitivity Analysis Report (FR-006)
├── data/
│   ├── raw/                 # Simulation logs (time-series)
│   └── processed/           # Aggregated metrics
├── cli/
│   └── run_simulation.py    # Main entry point for parameter sweeps
└── tests/
    ├── unit/
    │   └── test_eco_director.py
    └── integration/
        └── test_simulation_pipeline.py

requirements.txt
```

**Structure Decision**: Single project structure selected. The `src/sim` module isolates the simulation logic (CA vs. Neural) to ensure strict versioned interface compliance (Constitution Principle VI). The `src/analysis` module separates statistical validation from simulation execution, ensuring reproducibility and modularity. The `physics_oracle.py` enforces the `physics_oracle.schema.yaml` contract.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Linear Mixed-Effects Model (LMM)** | Required to account for temporal autocorrelation and stochastic variance (noise_seed) in time-series data (FR-004, US-2). | Standard ANOVA assumes independence of observations, which is violated by time-series data, leading to inflated Type I errors. |
| **Random Forest Analysis** | Required to detect non-linear interactions between CA parameters that LMM might miss (FR-009). | LMM assumes linear relationships; non-linear parameter interactions (e.g., memory depth × non-linearity) require a tree-based approach. |
| **Physics Oracle (Stochastic Sandbox)** | Required to validate coherence against external, uncontrolled constraints, not tautological rules (FR-008). | Validating against the neural baseline alone would be circular reasoning. A deterministic oracle would make the CA tautological. |
| **Sensitivity Analysis (`sensitivity.py`)** | Required to sweep decision cutoffs and report inconsistency rates (FR-006). | Single threshold analysis fails to capture robustness of the metric definition. |
| **Partial Correlation Analysis** | Required to ensure metrics are not coupled to input state generation (SC-006). | Standard correlation does not control for confounding variables. |

| Schema | Enforced By | Purpose |
|--------|-------------|---------|
| `physics_oracle.schema.yaml` | `src/sim/physics_oracle.py` | Validates external physics constraints and noise injection outputs. |
