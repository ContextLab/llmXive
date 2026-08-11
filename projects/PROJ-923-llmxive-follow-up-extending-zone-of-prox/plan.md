# Project Plan: llmXive Follow-up - Extending "Zone of Proximal Policy Optimization"

## Overview
This project implements a follow-up study to the "Zone of Proximal Policy Optimization: Teacher in Prompts, Not Gradient" paper. The core innovation is the Confidence-Adaptive Pruning (CAP) mechanism, which dynamically adjusts the negative candidate set in prompts based on student confidence history.

## Objectives
1. Replicate the original ZPPO baseline using a static Negative Candidate-included Question (NCQ) prompt.
2. Implement the CAP mechanism to prune "consistently rejected" and "consistently accepted" candidates.
3. Conduct a statistical comparison (100 runs) to evaluate data efficiency (AUCC) and final performance.

## Project Structure
```
projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/
├── code/
│ ├── analysis/
│ │ ├── metrics.py
│ │ ├── report.py
│ │ ├── stats.py
│ │ ├── validate_metrics.py
│ │ └── validate_results.py
│ ├── data/
│ │ ├── generators.py
│ │ └── loaders.py
│ ├── loops/
│ │ ├── base_zppo.py
│ │ └── cap_zppo.py
│ ├── models/
│ │ ├── cap_classifier.py
│ │ ├── state_store.py
│ │ └── student_sim.py
│ ├── utils/
│ │ ├── logging.py
│ │ ├── noise.py
│ │ ├── seeds.py
│ │ └── validation.py
│ ├── config.py
│ ├── main.py
│ └── versioning.py
├── contracts/
│ ├── rollout_log.schema.yaml
│ ├── run_metadata.schema.yaml
│ ├── aggregated_metrics.schema.yaml
│ └── convergence_result.schema.yaml
├── data/
│ ├── raw/
│ ├── processed/
│ └── metrics/
├── specs/
│ └── 001-llmxive-zppo-extension/
├── state/
│ └── projects/
├── tests/
│ ├── contract/
│ ├── integration/
│ └── unit/
├── requirements.txt
├── ruff.toml
└── README.md
```

## Key Components
- **CAP Classifier**: Analyzes historical confidence scores to classify candidates (rejected, fluctuating, accepted).
- **Dynamic NCQ Generator**: Constructs prompts by excluding pruned candidates.
- **Simulation Engine**: Orchestrates 100 runs (10 tasks x 10 seeds) for statistical significance.
- **State Store**: Persists cycle records for CAP analysis.

## Dependencies
- Python 3.9+
- `datasets` (HuggingFace)
- `scikit-learn`
- `scipy`
- `pandas`
- `numpy`
- `matplotlib`
- `pyyaml`
- `jsonschema`

## Execution Flow
1. **Setup**: Initialize project structure and dependencies.
2. **Foundation**: Define schema contracts and utility functions.
3. **Baseline**: Run static ZPPO simulation (T012-T018).
4. **CAP**: Run CAP-ZPPO simulation (T022-T025).
5. **Analysis**: Perform statistical comparison (T029-T033).
6. **Validation**: Verify results against schemas.

## Constraints
- **Data Integrity**: All data loaders must use real sources (MMLU) or fail loudly.
- **Reproducibility**: Deterministic seed management (T008).
- **Compute**: Simulation must complete within 6 hours on CPU.
- **Noise**: Per-step Gaussian noise injection (σ=0.05) as per FR-008.

## Milestones
- **MVP**: User Story 1 (Static Baseline) complete.
- **Feature Complete**: User Story 2 (CAP) complete.
- **Analysis**: User Story 3 (Statistical Comparison) complete.
- **Polish**: Cross-cutting concerns and validation.
