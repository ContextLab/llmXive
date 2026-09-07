# Implementation Plan: llmXive follow-up: extending "Trust Region Policy Distillation"

**Branch**: `001-llmxive-topd-extension` | **Date**: 2026-09-07 | **Spec**: `specs/001-llmxive-topd-extension/spec.md`
**Input**: Feature specification from `specs/001-llmxive-topd-extension/spec.md`

## Summary

This feature implements a deterministic synthetic "Reasoning MDP" environment and a Trust Region Policy Distillation (TOP-D) training loop to investigate the collapse of reasoning strategies into shallow heuristics. The system will vary the interpolation coefficient $\alpha$ and student cognitive horizon to measure their interaction effect on effective reasoning depth. The implementation is strictly CPU-first, relying on `numpy` and `scipy` (for Tobit regression) to ensure compatibility with GitHub Actions free-tier runners, avoiding any external model dependencies or GPU requirements.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `matplotlib`, `pytest`  
**Storage**: In-memory data structures; training logs written to `data/raw/` as CSV/Parquet.  
**Testing**: `pytest` (unit tests for environment transitions; integration tests for training loops).  
**Target Platform**: Linux (GitHub Actions free-tier: vCPU, ~7 GB RAM).  
**Project Type**: Research Simulation / CLI Tool  
**Performance Goals**: Complete experimental grid (5 $\alpha$ values $\times$ 3 horizons $\times$ 100 episodes) within 6 hours.  
**Constraints**: No GPU; no external LLM API calls; deterministic random seeds; synthetic environment only (no real dataset ingestion required for the core logic, though reference datasets exist for context).  
**Scale/Scope**: A substantial number of total training episodes.; <100 MB memory footprint during execution.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds will be pinned in `code/`. All dependencies pinned in `requirements.txt`. |
| **II. Verified Accuracy** | **PASS** | No external citations required for the synthetic environment logic; statistical methods (Tobit) are standard. |
| **III. Data Hygiene** | **PASS** | Training logs will be checksummed; raw data preserved; no PII (synthetic data). |
| **IV. Single Source of Truth** | **PASS** | All metrics (depth, stability) will be derived directly from `data/raw/` logs, not hand-typed. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes; state file updated on completion. |
| **VI. Cognitive Horizon Alignment** | **PASS** | The design explicitly treats `horizon` and `alpha` as independent variables to isolate the interaction effect. |
| **VII. Deterministic Synthetic Validation** | **PASS** | The "Reasoning MDP" is implemented as a deterministic graph traversal with known ground-truth paths. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-topd-extension/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-1050-llmxive-follow-up-extending-trust-region/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── env/
│   │   ├── __init__.py
│   │   ├── reasoning_mdp.py       # FR-001: Synthetic MDP implementation
│   │   └── teacher_policy.py      # FR-001: Ground-truth path generator
│   ├── student/
│   │   ├── __init__.py
│   │   ├── policy.py              # FR-002: Student policy with horizon
│   │   └── topd_loss.py           # FR-003: TOP-D loss calculation
│   ├── experiments/
│   │   ├── __init__.py
│   │   ├── runner.py              # FR-004: Training loop & logging
│   │   └── grid_config.py         # Configuration for alpha/horizon sweep
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── tobit_model.py         # FR-005: Censored regression (Tobit)
│   └── main.py                    # Entry point for the experimental grid
├── data/
│   ├── raw/                       # Training logs (CSV/Parquet)
│   └── processed/                 # Aggregated results for analysis
├── tests/
│   ├── unit/
│   │   ├── test_mdp.py
│   │   └── test_loss.py
│   └── integration/
│       └── test_training_loop.py
└── docs/
    └── results/                   # Generated plots and reports
```

**Structure Decision**: Selected a modular, package-based structure (`code/env`, `code/student`, etc.) to strictly separate the environment logic from the training loop and statistical analysis. This ensures the "Reasoning MDP" can be tested independently (US-1) and the statistical analysis can be run on any valid log file (US-3).

## Complexity Tracking

No violations detected. The design adheres to the CPU-first constraint by avoiding large model weights and using tabular/tiny-network approaches for the student policy.
