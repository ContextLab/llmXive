# Dream-State Learning: REM-like Consolidation in Language Models

## Overview

This project implements a novel training paradigm for language models that mimics the biological processes of REM sleep to enhance memory consolidation. By alternating between "Wake" (supervised fine-tuning on real data) and "Dream" (denoising autoencoder reconstruction of masked inputs) phases, the model learns more robust representations.

## Core Concepts

### Wake Phase
Standard supervised fine-tuning on real GLUE/SuperGLUE datasets using cross-entropy loss. The model learns to predict next tokens from actual text sequences.

### Dream Phase
The model generates masked inputs and attempts to reconstruct the original tokens. This Denoising Autoencoder (DAE) approach encourages the model to learn deeper semantic relationships and improve generalization.

### Consolidation Mechanism
The "consolidated" state in this digital system is defined as:
1. **Stable Weight Configuration**: Model weights that minimize both wake-phase loss and dream-phase reconstruction error
2. **Entropy Control**: Outputs maintain entropy above a threshold (0.5 bits), preventing collapse to low-diversity patterns
3. **Memory Replay**: Periodic reconstruction of previously seen patterns strengthens long-term retention

## Project Structure

```
PROJ-589-dream-state-learning-implementing-rem-li/
├── code/
│ ├── config.py # Hyperparameters and configuration
│ ├── main.py # Entry point for training and evaluation
│ ├── data/
│ │ ├── augment.py # DAE masking logic
│ │ └── loader.py # Dataset loading with checksum verification
│ ├── models/
│ │ ├── trainer.py # Core wake/dream training loop
│ │ └── __init__.py # Model initialization
│ ├── eval/
│ │ ├── metrics.py # Evaluation metrics and statistical tests
│ │ ├── reporting.py # Result reporting and visualization
│ │ ├── sensitivity_report.py # Temperature sweep analysis
│ │ └── statistical_analysis.py # Wilcoxon signed-rank tests
│ ├── utils/
│ │ ├── logger.py # Structured logging
│ │ ├── memory_monitor.py # Memory usage tracking and limits
│ │ └── exceptions.py # Custom exceptions
│ └── scripts/
│ ├── generate_final_report.py
│ └── verify_feasibility.sh
├── data/
│ ├── raw/ # Downloaded datasets
│ ├── checkpoints/ # Model checkpoints
│ ├── results/ # Evaluation results
│ └── logs/ # Training logs
├── tests/
│ ├── unit/ # Unit tests
│ ├── integration/ # Integration tests
│ └── contract/ # Schema validation tests
├── docs/
│ └── README.md # This file
├── quickstart.md # Quick start guide
└── requirements.txt # Python dependencies
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PROJ-589-dream-state-learning-implementing-rem-li
```

2. Install dependencies:
```bash
pip install -r code/requirements.txt
```

## Quick Start

See [quickstart.md](../quickstart.md) for detailed instructions on running the training pipeline.

## Configuration

Key hyperparameters are defined in `code/config.py`:
- `WAKE_DREAM_RATIO`: Ratio of wake to dream steps (default 4:1)
- `MASK_RATE`: Probability of token masking in dream phase
- `ENTROPY_THRESHOLD`: Minimum entropy for valid outputs (0.5 bits)
- `WARMUP_STEPS`: Number of steps before dream phase begins (10)
- `MAX_WALL_CLOCK_HOURS`: Maximum training time (5 hours)

## Running Experiments

### Single Seed Experiment
```bash
python code/main.py --seed 42 --dataset glue-sst2 --epochs 1
```

### Temperature Sweep
```bash
python code/main.py --temperature-sweep --temps 0.5,0.7,0.9
```

### Baseline Comparison
```bash
python code/main.py --baseline --dataset glue-sst2
```

## Evaluation

The project implements:
- Few-shot accuracy on held-out GLUE/SuperGLUE subsets
- Wilcoxon signed-rank test for statistical significance (α=0.05)
- Temperature sensitivity analysis
- Memory and time constraint verification

## Results

Results are saved to:
- `data/results/comparison_report.json`: Comparative analysis between experimental and baseline models
- `data/results/sensitivity_report.json`: Temperature sweep variance analysis
- `data/logs/`: Structured JSON logs of training events

## Contributing

1. Create a feature branch
2. Implement changes following the existing code structure
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License
