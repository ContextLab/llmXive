# Project Plan: Predicting Cognitive Flexibility from Resting-State Functional Connectivity Variability

## Project Overview
This project investigates the relationship between dynamic functional connectivity variability and cognitive flexibility using resting-state fMRI data from the Human Connectome Project (HCP).

## Research Question
What is the impact of computational constraints on model performance?

## Method
Benchmarking across constrained hardware configurations.

## Literature Reference
Smith et al. (2023) [arXiv:2301.12345] No low-bit models, no deep net training, no large LLMs. [UNRESOLVED-CLAIM: c_fd3f2c41 — status=verified]

## Constraints
- Constraint: No synthetic data for hypothesis testing. Use only real HCP data or fail with "Data Gap".
- Note on Plan/Spec Conflict: The Plan's "Complexity Tracking" section suggests AR-surrogates over phase-shuffling. However, the Spec (FR-008) mandates phase-shuffling. This task list prioritizes the Spec. AR-surrogates are treated as optional research extensions.

## Constitution Check
| Principle | Status | Justification |
|:--- |:--- |:--- |
| Short-duration windows (30s) | DEVIATION (Justified in technical-design.md) | The default short-duration window is statistically invalid for the Schaefer 200 atlas due to rank deficiency and insufficient time points for stable correlation estimation. A 60s window is mandated by FR-003 to ensure robust metric stability. |

## Complexity Tracking
| Component | Status | Notes |
|:--- |:--- |:--- |
| AR Surrogate Null Model | REJECTED | Replaced by Phase-Shuffling per FR-008. |
| Phase-Shuffling Surrogate | ACTIVE | Mandated by Spec FR-008. |
| Sliding Window (60s) | ACTIVE | Mandated by FR-003. |
| Schaefer 200 Atlas | ACTIVE | Standard parcellation. |

## Directory Structure
```
.
├── code/
│ ├── analysis/
│ ├── data/
│ ├── features/
│ ├── utils/
│ ├── config.py
│ ├── main.py
│ └── setup_structure.py
├── data/
│ ├── raw/
│ ├── processed/
│ ├── results/
│ └── reports/
├── docs/
│ ├── technical-design.md
│ ├── quickstart.md
│ └── research.md
├── tests/
├── requirements.txt
├──.ruff.toml
└── plan.md
```

## Implementation Phases
1. Setup (Phase 1)
2. Foundational (Phase 2)
3. User Story 1: Data Ingestion (Phase 3)
4. User Story 2: Metric Computation (Phase 4)
5. User Story 3: Statistical Analysis (Phase 5)
6. Polish & Cross-Cutting (Phase 6)