# llmXive: Dynamic Socio-Cognitive State Injection

A research pipeline for investigating the impact of dynamic socio-cognitive state injection on LLM-mediated conflict resolution.

## Project Overview

This project implements a CPU-only pipeline to generate conflict trajectories, train a lightweight state classifier, and execute paired mediation experiments comparing **Dynamic Adapter** (state-injected) vs. **Static Baseline** (no injection) conditions.

### Key Features
- **Synthetic Data Generation**: Oversampled conflict trajectories targeting high emotional reactivity and diverse cultural identity.
- **Dynamic State Injection**: Real-time socio-cognitive state detection and prompt injection during inference.
- **Statistical Rigor**: Paired t-tests/Wilcoxon signed-rank tests with Holm-Bonferroni correction for multiple comparisons.
- **CPU-Only Execution**: Designed for reproducibility on standard hardware without GPU dependencies.

## Quick Start

See `specs/001-dynamic-state-injection/quickstart.md` for detailed setup and execution instructions.

```bash
# 1. Install dependencies (CPU-only)
pip install -r requirements.txt

# 2. Generate conflict trajectories
python code/data/generator.py

# 3. Train the state classifier
python code/models/classifier.py

# 4. Run the experiment suite (Adapter vs. Static)
python code/experiments/runner.py

# 5. Analyze results
python code/analysis/stats.py
```

## Project Structure

```
.
├── code/
│ ├── analysis/ # Metrics, stats, performance monitoring
│ ├── data/ # Trajectory generation and loading
│ ├── experiments/ # Runner, prompts, retry logic
│ ├── models/ # Classifier, evaluator, entities
│ ├── config.py # Global configuration
│ └── setup_structure.py # Directory initialization
├── data/
│ ├── raw/ # Raw input data (if any)
│ ├── processed/ # Generated trajectories, experiment logs
│ └── results/ # Statistical reports, performance metrics
├── specs/
│ └── 001-dynamic-state-injection/
│ ├── spec.md # Feature specification
│ ├── plan.md # Implementation plan
│ └── quickstart.md # Execution guide
├── tests/ # Unit, contract, and integration tests
├── requirements.txt
└── README.md
```

## User Stories

1. **US1 (P1)**: Generate Conflict Trajectories with Targeted Oversampling
2. **US2 (P2)**: Execute Paired Mediation Experiments (Adapter vs. Static)
3. **US3 (P3)**: Compute Consensus Gap Closure and Statistical Significance

## Constraints & Requirements

- **FR-004**: CPU-only execution. No `bitsandbytes`, `flash-attn`, or CUDA dependencies.
- **FR-002**: Classifier must be trained on turn-level dialogue text, not evaluator scores.
- **SC-003**: Performance metrics (throughput/latency) must be logged and reported.
- **SC-005**: Sensitivity analysis on classifier confidence thresholds.

## License

Research use only.
