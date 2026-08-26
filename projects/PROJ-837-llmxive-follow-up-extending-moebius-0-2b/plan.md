# Project Plan: llmXive Follow-up - Extending Moebius 0.2B

## Overview
This project implements a dynamic rank adjustment mechanism for the Moebius 0.2B image inpainting model, optimizing for CPU efficiency while maintaining fidelity. The core innovation is a lightweight gating head that predicts mask complexity and modulates the linear low-rank matrices ($L\lambda MI$) accordingly.

## Objectives
1. **Data Independence**: Establish ground truth complexity labels decoupled from model metrics (CI Mode: random proxy; Research Mode: human annotations).
2. **Proxy Validation**: Verify correlation between synthetic mask metrics and ground truth (Gate: $r \ge 0.7$ for human data).
3. **Dynamic Architecture**: Implement `Moebius-Dynamic` with a $\le 5M$ parameter gating head.
4. **Efficiency**: Achieve $\ge 30\%$ latency reduction on low-complexity masks with $\Delta FID \le 0.5$.

## User Stories
- **US1**: Data Preparation & Human Complexity Annotation (P1)
- **US4**: Synthetic Proxy Validation (P2) - Gates US2
- **US2**: Dynamic Rank Adjustment Mechanism (P2)
- **US3**: Efficiency & Fidelity Evaluation (P3)

## Directory Structure
```
projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/
├── plan.md # This file
├── specs/ # Feature specifications
│ └── 001-llmxive-moebius-dynamic/
├── code/
│ ├── config.py # Mode flags, paths, hyperparameters
│ ├── config_env.py # Environment configuration & artifact hashing
│ ├── data/
│ │ ├── loader.py # Places365 fetcher
│ │ ├── mask_generator.py
│ │ └── annotator.py # CI/Research scoring logic
│ ├── models/
│ │ ├── data_models.py # Pydantic/Attrs data classes
│ │ ├── moebius_tiny.py
│ │ ├── gating_head.py
│ │ └── moebius_dynamic.py
│ ├── training/
│ │ ├── train_gating.py
│ │ └── train_end_to_end.py
│ ├── eval/
│ │ ├── metrics.py # FID, LPIPS, Latency
│ │ ├── stats.py # Correlation, Power analysis
│ │ └── report.py
│ └── utils/
│ ├── seed.py
│ ├── logger.py
│ └── cpu_profiler.py
├── data/
│ ├── raw/ # Downloaded datasets
│ ├── processed/
│ │ └── masked_images/
│ └── annotations/ # Scores, validation logs
├── tests/
│ ├── unit/
│ └── integration/
├── requirements.txt
└── pyproject.toml
```

## Constraints
- **Hardware**: CPU-only execution (CI/Research). No CUDA.
- **Memory**: Target < 7GB RAM, < 14GB Disk.
- **Data Integrity**: No synthetic input data; real datasets only (Places365 via HF).
- **Circularity**: CI Mode scores must be random/uniform; Research Mode must use external human data.

## Execution Flow
1. **Setup**: Initialize environment, download Places365 subset.
2. **Data Prep (US1)**: Generate masks, compute synthetic metrics, assign ground truth (CI or Research).
3. **Validation (US4)**: Check correlation. Block if $r < 0.7$ (Research) or log expected (CI).
4. **Model (US2)**: Train Gating Head + Moebius Dynamic.
5. **Eval (US3)**: Benchmark latency/FID, generate report.

## Dependencies
- Python 3.9+
- PyTorch (CPU)
- `datasets` (HuggingFace)
- `scikit-learn`, `pandas`, `numpy`, `pillow`
- `lpips`, `torchmetrics`, `torchvision`
- `ruff`, `black`
