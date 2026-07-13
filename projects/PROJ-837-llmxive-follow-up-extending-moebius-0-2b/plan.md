# Project Plan: llmXive Follow-up - Extending Moebius 0.2B

## Overview
This project extends the "Moebius: 0.2B Lightweight Image Inpainting Framework" with a dynamic rank adjustment mechanism (Moebius-Dynamic). The goal is to create a CPU-efficient model that adapts its computational rank based on mask complexity, validated against human annotations or decoupled synthetic proxies.

## Objectives
1. Implement a dynamic gating mechanism to modulate model rank based on input complexity.
2. Establish a rigorous data pipeline for generating and validating mask complexity scores.
3. Ensure all training and evaluation runs on CPU-only infrastructure with strict memory limits.
4. Validate the synthetic proxy for complexity against human annotations (Research Mode) or strict decoupled simulation (CI Mode).

## Directory Structure
The project follows this layout:
- `code/`: Source code for models, data pipelines, training, and evaluation.
- `data/`: Raw, processed, and artifact data.
- `tests/`: Unit and integration tests.
- `specs/`: Design documents and user stories.
- `data/results/`: Evaluation metrics, logs, and validation reports.
- `data/annotations/`: Human or synthetic complexity scores.
- `data/processed/`: Masked images and intermediate data.
- `projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/`: This project's specific plan and metadata.

## Phases
1. **Setup**: Project initialization, dependencies, and tooling.
2. **Foundational**: Core utilities (seeding, logging, profiling, config).
3. **User Story 1 (Data)**: Data loading, mask generation, and annotation (CI/Research modes).
4. **User Story 4 (Validation)**: Proxy validation gate (correlation check).
5. **User Story 2 (Model)**: Dynamic rank mechanism implementation.
6. **User Story 3 (Evaluation)**: Efficiency and fidelity benchmarking.
7. **Polish**: Documentation and final report generation.

## Constraints
- **CPU Only**: No CUDA. All code must run on standard CPU cores.
- **Memory**: Target < 8GB RAM usage during training/evaluation.
- **No Circularity**: Ground truth scores must be decoupled from model metrics in CI mode.
- **Reproducibility**: Deterministic seeding for all random operations.

## Dependencies
- Python 3.9+
- PyTorch (CPU)
- scikit-learn, pandas, numpy, scipy
- datasets (HuggingFace)
- lpips, torchmetrics, torchvision
- ruff, black (dev)
