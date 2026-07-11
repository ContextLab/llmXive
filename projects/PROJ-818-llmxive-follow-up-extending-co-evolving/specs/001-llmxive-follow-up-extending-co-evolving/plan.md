# Implementation Plan: Co-Evolving Policy Distillation

**Branch**: `001-coevolving-policy-distillation` | **Date**: 2026-07-11 | **Spec**: `specs/001-coevolving-policy-distillation/spec.md`
**Input**: Feature specification from `/specs/001-coevolving-policy-distillation/spec.md`

## Summary

This feature implements a comparative study of three training strategies (Sequential, Mixed-task, Co-evolving) for non-differentiable reasoning tasks. The core objective is to measure the mitigation of catastrophic forgetting in discrete domains (propositional logic and grid-world navigation) using evolutionary strategies (ES) rather than gradient-based backpropagation. The system generates synthetic datasets via `sympy` and `networkx`, executes a CPU-tractable evolutionary training loop with strict parity in data exposure, and performs statistical analysis (Mixed-Design ANOVA/Tukey) on forgetting rates.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `sympy` (logic generation), `networkx` (grid generation), `numpy` (numerical ops), `scipy` (statistical tests), `pytest` (testing).  
**Storage**: Persistent `data/` directory for all generated artifacts. All files are checksummed and the checksums are recorded in `data/checksums.json`. No persistent database.  
**Testing**: `pytest` with contract tests validating schema compliance and statistical output.  
**Target Platform**: Linux (GitHub Actions Free Tier: limited CPU, 7GB RAM, no GPU).  
**Project Type**: Research CLI / Simulation Engine.  
**Performance Goals**: Complete 30+ runs per condition (total ~90+ runs) within 6 hours; memory footprint < 4GB.  
**Constraints**: No GPU usage; strict integer parity for rule evaluations; deterministic seeding.  
**Scale/Scope**: Synthetic dataset generation (~ tasks per domain); 3 experimental conditions; statistical analysis of forgetting metrics.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Reference |
|-----------|--------|-----------|
| **I. Reproducibility** | PASS | Plan mandates pinned seeds in `code/` and deterministic synthetic generation. |
| **II. Verified Accuracy** | PASS | No external citations required for the core logic; `sympy`/`networkx` are standard libraries. |
| **III. Data Hygiene** | PASS | Synthetic data is written to `data/` and checksums recorded in `data/checksums.json` as required. |
| **IV. Single Source of Truth** | PASS | Forgetting metrics derived strictly from `data/` artifacts and `code/` logic. |
| **V. Versioning Discipline** | PASS | Plan includes content hashing for generated datasets and code artifacts. |
| **VI. Non-Differentiable Training** | PASS | Explicitly uses Evolutionary Strategies (ES); no backpropagation; relies on `sympy`/`networkx`. |
| **VII. Cross-Task Retention** | PASS | Forgetting rate defined as accuracy drop (initial single-task vs. final multi-task); **Mixed-Design ANOVA** mandated per Constitution Principle VII. |

## Project Structure

### Documentation (this feature)

```text
specs/001-coevolving-policy-distillation/
├── plan.md              # This file (Phase 0)
├── research.md          # Phase 0 output (Methodology)
├── data-model.md        # Phase 0 output (Data Schemas)
├── quickstart.md        # Phase 0 output (Usage Guide)
└── contracts/           # Phase 0 output (Prerequisite for Implementation)
    ├── dataset.schema.yaml
    ├── agent_state.schema.yaml
    └── result.schema.yaml
```

> **Note on Contracts**: Contract definitions are a **Phase 0 prerequisite** for the implementation phase. They are generated now to ensure the `Testing` section referenced in this plan and the subsequent implementation can validate against them immediately.

### Source Code (repository root)

```text
src/
├── generators/
│   ├── logic_generator.py      # sympy-based proof generation
│   └── grid_generator.py       # networkx-based navigation generation
├── agents/
│   ├── base_agent.py           # Abstract agent with rule-set management
│   ├── sequential_agent.py     # Sequential training logic
│   ├── mixed_agent.py          # Mixed-task training logic
│   └── coevolving_agent.py     # Co-evolving logic with bidirectional exchange
├── analysis/
│   ├── forgetting_metrics.py   # Calculation of retention/drop rates
│   └── statistical_tests.py    # Mixed-Design ANOVA and Tukey implementation
├── utils/
│   ├── config.py               # Seeding and parameter loading
│   └── checksums.py            # Data integrity verification
└── cli.py                      # Entry point for running experiments

tests/
├── contract/
│   ├── test_dataset_schema.py
│   └── test_result_schema.py
├── unit/
│   ├── test_logic_generation.py
│   └── test_agent_conditions.py
└── integration/
    └── test_full_pipeline.py
```

**Structure Decision**: Single project structure selected. The research workflow is linear (Generate -> Train -> Evaluate -> Analyze), making a monolithic `src/` directory with clear sub-packages (`generators`, `agents`, `analysis`) the most maintainable approach for a simulation engine. No frontend or separate backend is required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Multiple Agent Classes** | Required to isolate the "Co-evolving" mechanism from "Sequential" and "Mixed" baselines. | A single agent with a flag would obscure the distinct state management and exchange logic needed for the co-evolutionary step. |
| **Strict Checksumming** | Required by Constitution Principle III for reproducibility of synthetic data. | Skipping checksums would violate the "Verified Accuracy" gate, as regenerated data might drift if parameters change. |
| **Statistical Rigor (Mixed-Design ANOVA)** | Required by SC-004, SC-006, and Constitution Principle VII to validate significance across 3+ groups with repeated measures. | A simple t-test or One-way ANOVA would be statistically invalid for comparing three conditions with within-subjects factors (increased Type I error, violation of independence). |

