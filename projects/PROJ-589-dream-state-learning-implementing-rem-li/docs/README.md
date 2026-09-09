# Dream-State Learning: REM-like Consolidation in Language Models

## Overview

This project implements a novel training paradigm for language models that mimics the biological processes of REM (Rapid Eye Movement) sleep and memory consolidation. The core hypothesis is that alternating "wake" (supervised fine-tuning) and "dream" (denoising autoencoder on masked real data) phases can improve model robustness and generalization compared to continuous supervised training.

## Architecture

### Wake Phase
- Standard supervised fine-tuning on real GLUE/SuperGLUE data
- Cross-entropy loss with AdamW optimizer
- Batching via PyTorch DataLoader

### Dream Phase
- Denoising Autoencoder (DAE) on masked real data
- Random token masking at 15% rate (BERT-style)
- Reconstruction loss via cross-entropy
- Multi-to-one wake-to-dream step ratio (5:1 by default)

### Key Features
- **Warm-up Protocol**: Dream phase disabled for first 10 training steps
- **Entropy Checks**: Low-entropy outputs (<0.5 bits/token) trigger retry or batch discard
- **Memory Monitoring**: Hard abort on OOM with checkpoint save
- **Statistical Comparison**: Paired t-test against continuous-training baseline
- **Sensitivity Analysis**: Temperature sweep with variance reporting

## Project Structure

```
code/
├── config.py # Hyperparameters and configuration
├── main.py # Orchestration and experiment runner
├── data/
│ ├── augment.py # DAE masking logic
│ └── loader.py # GLUE/SuperGLUE data loading
├── models/
│ ├── trainer.py # Wake/dream training loop
│ └── __init__.py # Model initialization
├── eval/
│ ├── metrics.py # Accuracy and evaluation metrics
│ ├── statistical_analysis.py # Paired t-test and statistical comparison
│ ├── sensitivity_report.py # Temperature sweep analysis
│ └── reporting.py # Result reporting and visualization
├── utils/
│ ├── logger.py # Structured logging
│ ├── memory_monitor.py # Memory tracking and OOM enforcement
│ └── exceptions.py # Custom exceptions
└── scripts/
 ├── cleanup_and_refactor.py # Code cleanup utilities
 ├── generate_final_report.py # Final report generation
 └── validate_quickstart.py # Quickstart validation

data/
├── raw/ # Raw dataset downloads
├── checkpoints/ # Model checkpoints
├── results/ # Evaluation results and reports
└── logs/ # Training logs

tests/
├── unit/ # Unit tests
├── integration/ # Integration tests
└── contract/ # Schema validation tests
```

## Quick Start

### Prerequisites
- Python 3.8+
- pip package manager
- 8GB+ RAM (for CPU-only training)

### Installation
```bash
cd code
pip install -r requirements.txt
```

### Running a Single Experiment
```bash
python main.py --glue_subset=mrpc --seeds=5 --warmup_steps=10
```

### Running Temperature Sensitivity Analysis
```bash
python main.py --temperature_sweep --temperatures=0.5,0.7,0.9 --seeds_per_temp=5
```

### Validation
```bash
python scripts/validate_quickstart.py
```

## Configuration

Key hyperparameters in `config.py`:
- `MASK_RATE`: 0.15 (15% token masking for dream phase)
- `WARMUP_STEPS`: 10 (minimum steps before dream phase)
- `DREAM_RATIO`: 5 (wake steps per dream step)
- `ENTROPY_THRESHOLD`: 0.5 (bits per token)
- `MAX_WALL_CLOCK_HOURS`: 5.5 (runtime limit)
- `MEMORY_LIMIT_GB`: 8 (RAM limit)

## Results

After training, results are saved to:
- `data/results/comparison_report.json`: Experimental vs. baseline comparison
- `data/results/variance_report.json`: Temperature sweep variance analysis
- `data/logs/`: Structured JSON logs of training events

## Limitations

- CPU-only execution (no GPU support)
- Limited to small GLUE/SuperGLUE subsets for CI compatibility
- Memory-constrained environment (8GB RAM limit)

## References

This implementation follows the design specifications in:
- `specs/001-dream-state-learning-implementing-rem-li/spec.md`
- `specs/001-dream-state-learning-implementing-rem-li/plan.md`

## Contributing

1. Ensure all unit and integration tests pass
2. Run `scripts/validate_quickstart.py` before committing
3. Follow the existing code style (black formatting, ruff linting)

## License

Research code for academic purposes.