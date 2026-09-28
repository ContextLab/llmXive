# Project Plan: llmXive Follow-up: Extending "Zone of Proximal Policy Optimization"

## Overview
This project extends the original ZPPO (Zone of Proximal Policy Optimization) paper by implementing a Confidence-Adaptive Pruning (CAP) mechanism. The goal is to dynamically prune negative candidates from the prompt based on student confidence history, rather than using a static set of failure modes.

## Objectives
1. Reproduce the baseline ZPPO convergence curve using a static Negative Candidate-included Question (NCQ) prompt.
2. Implement the CAP mechanism to prune "consistently rejected" and "consistently accepted" candidates.
3. Compare data efficiency (AUCC) and final performance between Baseline and CAP-ZPPO.

## User Stories
- **US1 (P1)**: Static Baseline Simulation. Simulate original ZPPO loop with static NCQ.
- **US2 (P2)**: Confidence-Adaptive Pruning. Implement CAP logic to filter candidates dynamically.
- **US3 (P3)**: Comparative Statistical Analysis. Run batch experiments and perform t-tests.

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
├── data/
│ ├── metrics/
│ │ └── batch_results.csv
│ └── rollouts/
├── contracts/
│ ├── rollout_log.schema.yaml
│ ├── run_metadata.schema.yaml
│ ├── aggregated_metrics.schema.yaml
│ └── convergence_result.schema.yaml
├── specs/
│ └── 001-llmxive-zppo-extension/
├── state/
│ └── projects/
│ └── PROJ-923-llmxive-follow-up-extending-zone-of-prox.yaml
├── tests/
│ ├── contract/
│ ├── unit/
│ └── integration/
├── requirements.txt
└── README.md
```

## Dependencies
- numpy
- pandas
- scikit-learn
- tqdm
- pyyaml
- datasets
- pytest
- scipy
- matplotlib
- jsonschema

## Execution Flow
1. **Setup**: Initialize project structure and dependencies.
2. **Foundation**: Implement schema contracts, seed management, noise injection, and state store.
3. **US1**: Run baseline simulation (T018) to generate baseline metrics.
4. **US2**: Run CAP simulation (T025) to generate CAP metrics.
5. **US3**: Run batch experiment (T031) and generate comparative report (T032).

## Constitution Principles
- **I (Reproducibility)**: All random seeds managed via `utils/seeds.py`.
- **II (Transparency)**: All data generation and simulation steps logged.
- **III (Data Integrity)**: Real data loaders fail loudly; no synthetic fallbacks for training data.
- **IV (Verifiability)**: Results validated against schema contracts.
- **V (Versioning)**: Data checksums tracked in state file.
- **VI (Pruning)**: CAP explicitly excludes consistently accepted/rejected candidates.
