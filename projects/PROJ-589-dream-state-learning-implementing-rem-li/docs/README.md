# Dream-State Learning: REM-like Consolidation in Language Models

## Project Overview

This project implements a novel training paradigm for language models inspired by the biological mechanisms of REM (Rapid Eye Movement) sleep. The core hypothesis is that alternating between "Wake" (standard supervised fine-tuning) and "Dream" (Denoising Autoencoder-based reconstruction) phases enhances model consolidation and generalization.

## Key Concepts

### What is "Consolidated" in a Digital System?
Unlike biological systems where consolidation involves structural remodeling (protein synthesis, synaptic strengthening), in a digital neural network, a "consolidated" state is defined operationally as:
1. **Stability**: The model's performance on held-out validation data remains stable or improves after the Dream phase, despite the introduction of noise.
2. **Robustness**: The model's loss landscape becomes smoother, reducing sensitivity to input perturbations (measured via entropy checks).
3. **Generalization**: The model achieves lower perplexity on out-of-distribution samples compared to a baseline trained with continuous supervised fine-tuning (SFT) for the same token count.

### The Wake/Dream Cycle
- **Wake Phase**: Standard Cross-Entropy loss on real data (GLUE/SuperGLUE).
- **Dream Phase**: The model is presented with masked inputs (DAE) and tasked with reconstructing the original tokens. This forces the model to rely on learned internal representations rather than immediate context, mimicking memory replay.
- **Ratio**: A 4:1 ratio of Wake to Dream steps is enforced by the `DreamScheduler`.

## Architecture

The project is structured as follows:

```
code/
├── config.py # Hyperparameters, paths, seed management
├── main.py # Entry point, orchestration of experiments
├── data/
│ ├── loader.py # Real data loading (GLUE/SuperGLUE) with checksum verification
│ └── augment.py # DAE masking logic
├── models/
│ ├── trainer.py # Core Wake/Dream training loop, DreamScheduler
│ └── __init__.py # Model initialization (DistilBERT/TinyLlama)
├── eval/
│ ├── metrics.py # Accuracy, Wilcoxon statistical tests
│ ├── statistical_analysis.py # Comparative analysis logic
│ └── sensitivity_report.py # Temperature sweep analysis
├── utils/
│ ├── logger.py # Structured logging
│ ├── memory_monitor.py # RAM tracking and OOM enforcement
│ └── exceptions.py # Custom exceptions (DataIntegrityError, TimeLimitExceeded)
└── scripts/
 └── generate_final_report.py # Aggregates results from multiple seeds
```

## Usage

### Prerequisites
- Python 3.9+
- CPU-only environment (optimized for CI/GitHub Actions)
- Dependencies listed in `code/requirements.txt`

### Installation
```bash
cd code
pip install -r requirements.txt
```

### Running an Experiment
To run a single experiment with the default configuration:
```bash
python main.py --seed 42 --max-steps 100
```

To run the full comparative analysis (5 seeds, experimental vs. baseline):
```bash
python main.py --mode full_comparison
```

To run the temperature sensitivity sweep:
```bash
python main.py --mode temperature_sweep
```

### Output Artifacts
Results are saved to the `data/` directory:
- `data/results/comparison_report.json`: Statistical comparison between experimental and baseline models.
- `data/results/sensitivity_report.json`: Variance analysis across temperature settings.
- `data/logs/`: Structured JSON logs of training progress, phase transitions, and entropy metrics.
- `data/checkpoints/`: Model states saved upon completion or OOM events.

## Statistical Methodology

The primary success criterion is the **Wilcoxon signed-rank test** (α=0.05) comparing the accuracy of the Dream-State model against a continuous SFT baseline across 5 independent seeds. This non-parametric test is chosen due to the likely unequal variance between the two distributions.

## Constraints & Safety

- **Memory Limits**: The `MemoryMonitor` enforces a hard RAM limit (default 6GB). If exceeded, the process aborts and saves the current checkpoint.
- **Time Limits**: A wall-clock limit (default 5 hours) prevents runaway processes in CI environments.
- **Data Integrity**: All datasets are downloaded via the HuggingFace `datasets` library with SHA-256 checksum verification. Any mismatch triggers a `DataIntegrityError`.

## References

- Plan Constitution Principle VII: Statistical robustness via non-parametric testing.
- Biological Inspiration: REM sleep mechanisms in memory consolidation (Kandel et al., Dyson et al.).
