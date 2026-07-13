# Implementation Plan: llmXive follow-up: extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

**Branch**: `001-llmxive-density-horizon` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-density-horizon/spec.md`
**Input**: Feature specification from `specs/001-llmxive-density-horizon/spec.md`

## Summary

This feature implements a synthetic simulation pipeline to investigate how the **semantic density** of retrieved context modulates the **optimal masking horizon** for long-horizon search agents. The project generates **2,000** synthetic trajectories with controlled entropy and technical token ratios, simulates agent performance under varying retention windows using a stochastic "Focus Decay" model, and performs a logistic regression (GLM) with natural splines to quantify the interaction effect. The implementation is constrained to CPU-only execution on GitHub Actions free-tier runners (≤7 GB RAM, ≤14 GB disk, ≤6 h runtime).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn` (CPU-only), `scipy`  
**Storage**: Local JSON/CSV files under `data/` (streamed to disk to manage RAM)  
**Testing**: `pytest` (unit tests for entropy calculation, simulation logic, and regression output)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: CLI / Scientific Simulation  
**Performance Goals**: Generate [deferred] trajectories in < 10 mins; Regression fit in < 3 mins; Peak RAM < 7 GB.
**Constraints**: No GPU, no deep learning libraries (PyTorch/TensorFlow not required), no external API calls.  
**Scale/Scope**: [deferred] trajectories, Variable turns per trajectory, Multiple density levels, multiple horizon levels.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | Random seeds will be pinned in `code/`. All dependencies pinned in `requirements.txt`. |
| **II. Verified Accuracy** | ✅ Pass | No external citations used for internal design parameters (entropy thresholds, formulas). These are defined by the project's methodology as internal constants, not external sources. Principle II applies to external citations only; internal parameters are validated via unit tests against the defined methodology. |
| **III. Data Hygiene** | ✅ Pass | Generated data will be checksummed. Raw synthetic data preserved; analysis results derived to new files. |
| **IV. Single Source of Truth** | ✅ Pass | Regression coefficients and plots will be generated solely from `data/` via `code/`. |
| **V. Versioning Discipline** | ✅ Pass | Artifacts will carry content hashes in state files. |
| **VI. Semantic-Density Grounding** | ✅ Pass | The retention window size is dynamically adjusted based on the density of the critical evidence block. Specifically, the simulation calculates a `H_min` (minimum required horizon) derived from the density metric (FR-008). The masking policy explicitly references this `H_min` to determine if evidence is visible, ensuring alignment with the principle. |
| **VII. Synthetic Simulation Fidelity** | ✅ Pass | Simulator is rule-based; critical evidence injection is decoupled from agent output. The success logic is emergent via stochastic "Focus Decay", not hard-coded. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-density-horizon/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── trajectory.schema.yaml
│   └── regression_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-920-llmxive-follow-up-extending-masking-stal/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── generate_trajectories.py    # Implements US-1, FR-001, FR-008
│   ├── simulate_agent.py           # Implements US-2, FR-002, FR-009 (Revised Logic)
│   ├── analyze_results.py          # Implements US-3, FR-003, FR-006
│   ├── visualize_results.py        # Implements FR-004, FR-006
│   └── utils/
│       ├── entropy.py              # Entropy calculation logic
│       └── heuristics.py           # Heuristic solver logic
├── data/
│   ├── raw/                        # Generated synthetic trajectories (JSON)
│   └── processed/                  # Simulation logs and regression inputs (CSV)
├── tests/
│   ├── unit/
│   │   ├── test_entropy.py
│   │   └── test_simulator.py
│   └── integration/
│       └── test_pipeline.py
└── output/
    └── plots/                      # PNG surface plots
```

**Structure Decision**: Single-project structure chosen to minimize overhead. All logic is contained within `code/` with clear separation of concerns (generation, simulation, analysis, visualization). This aligns with the "Synthetic Simulation Fidelity" principle by keeping the data generation and analysis logic tightly coupled and reproducible.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Natural Splines in GLM** | Required to capture the complex interaction surface (piecewise regime shift) between horizon and success. | Standard linear terms would fail to model the non-linear "tipping point" where high density requires longer horizons. |
| **Streaming to Disk** | 2,000 trajectories + simulation logs could approach RAM limits if held in memory. | In-memory storage risks OOM on 7 GB limit; streaming ensures robustness. |
| **Composite Density Metric** | FR-008 defines density as entropy + technical tokens. | Pure entropy ignores domain-specific technicality; pure technical ratio ignores information density. |
| **[deferred] Trajectories** | Required for statistical power to detect interaction effect across 30 bins with natural splines. | A lower count results in approximately a small number of samples per bin, which is underpowered for logistic regression with splines. |
