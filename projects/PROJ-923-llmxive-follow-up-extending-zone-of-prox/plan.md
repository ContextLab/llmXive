# Project Plan: PROJ-923-llmxive-follow-up-extending-zone-of-prox

## Objective
Extend the ZPPO framework with Confidence-Adaptive Pruning (CAP) to improve data efficiency.

## Phases
1. **Setup**: Initialize project structure, dependencies, and linting.
2. **Foundational**: Implement schema contracts, seed management, noise injection, and state storage.
3. **User Story 1 (MVP)**: Static Baseline Simulation (ZPPO).
4. **User Story 2**: CAP Implementation (Dynamic Pruning).
5. **User Story 3**: Comparative Statistical Analysis.
6. **Polish**: Versioning, validation, and final reporting.

## Directory Structure
```
projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/
├── code/
│ ├── analysis/
│ ├── data/
│ ├── loops/
│ ├── models/
│ ├── utils/
│ ├── config.py
│ ├── main.py
│ └── versioning.py
├── data/
│ ├── metrics/
│ ├── plots/
│ └── raw/
├── contracts/
│ ├── rollout_log.schema.yaml
│ ├── run_metadata.schema.yaml
│ ├── aggregated_metrics.schema.yaml
│ └── convergence_result.schema.yaml
├── specs/
│ └── 001-llmxive-zppo-extension/
├── tests/
│ ├── contract/
│ ├── integration/
│ └── unit/
├── state/
├── requirements.txt
├── README.md
└── plan.md
```

## Execution Strategy
- Implement tasks in strict dependency order (Phase 1 -> 2 -> 3...).
- All data loaders must fail loudly if real data is missing (no synthetic fallbacks for training/held-out sets).
- Use `get_rng(seed)` factory for all random operations to ensure reproducibility.
