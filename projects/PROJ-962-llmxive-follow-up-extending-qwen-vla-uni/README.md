# llmXive: Non-Neural Approximation of VLA Priors

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Project Overview

This project implements a CPU-only pipeline to approximate the behavior of the Qwen-VLA (Vision-Language-Action) model using lightweight, non-neural models (Decision Trees and Gaussian Mixture Models). The goal is to evaluate whether interpretable, efficient models can achieve comparable performance to large neural networks while adhering to strict hardware constraints.

## Key Features

- **CPU-Only Execution**: Strict enforcement of CPU-only constraints for all stages (ingestion, training, inference, simulation).
- **Adaptive Clustering**: K-means clustering with adaptive k-reduction based on silhouette scores.
- **Streaming Data Processing**: Handles large datasets (>7GB) using streaming and Welford's algorithm for normalization.
- **Sequential Model Training**: Trains Decision Trees first, falling back to GMMs only if necessary to minimize computational cost.
- **Statistical Rigor**: Paired t-tests for continuous fidelity and binary success rates against VLA and random baselines.
- **No Synthetic Data**: All data is sourced from real datasets; the pipeline fails loudly if data cannot be fetched.

## Architecture

The pipeline consists of three main user stories:

1. **Dataset Ingestion and Clustering**: Ingests Qwen-VLA data, extracts kinematic features, and clusters trajectories.
2. **Model Training**: Generates BERT embeddings and trains Decision Trees or GMMs per cluster.
3. **Simulation and Evaluation**: Executes trajectories in simulation and performs statistical comparisons.

See `quickstart.md` for detailed execution instructions.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python code/09_run_final_validation.py --dataset qwen-vla/Hy-Embodied
```

## Documentation

- [Quickstart Guide](quickstart.md): Step-by-step execution instructions.
- [Research Methodology](research.md): Detailed methodology, model selection rationale, and constraints.
- [Task List](tasks.md): Complete list of implemented tasks and their status.

## Success Criteria

- **SC-001**: Trajectory fidelity ≥ 80% compared to VLA proxy.
- **SC-002**: Random baseline implemented via uniform sampling.
- **SC-003**: CPU-only execution (peak RAM ≤ 7GB).
- **SC-004**: Statistical significance (p < 0.05) in paired t-tests.
- **SC-005**: Clustering coverage ≥ 98%.

## Constraints

- **No GPU**: The pipeline is designed for CPU-only environments. GPU usage will cause the script to exit.
- **No Synthetic Data**: All data must be fetched from real sources. No placeholder data is used.
- **Memory Limits**: Streaming is used to handle large datasets within 7GB RAM constraints.

## Contributing

This is a research project. Contributions are welcome, but please adhere to the CPU-only and "no synthetic data" constraints.

## License

MIT License. See LICENSE file for details.
