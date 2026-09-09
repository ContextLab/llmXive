# Dream-State Learning: Quick Start Guide

## What is this?

This project implements a REM-like consolidation mechanism for language models.
Instead of continuous supervised fine-tuning, the model alternates between:
1. **Wake Phase**: Standard training on real data
2. **Dream Phase**: Denoising autoencoder training on masked real data

The hypothesis is that this alternating pattern improves consolidation and generalization,
similar to how biological sleep aids memory formation.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- 8GB+ RAM (required for CPU-only training)
- ~14GB disk space for datasets and checkpoints

## Installation

1. Clone the repository and navigate to the project root:
 ```bash
 git clone <repository-url>
 cd PROJ-589-dream-state-learning-implementing-rem-li
 ```

2. Install dependencies:
 ```bash
 cd code
 pip install -r requirements.txt
 ```

3. Verify installation:
 ```bash
 python -c "import torch; print(f'PyTorch {torch.__version__} installed')"
 ```

## Running Your First Experiment

### Basic Training Run

Run a minimal training job on the MRPC subset of GLUE:

```bash
cd code
python main.py --glue_subset=mrpc --seeds=1 --warmup_steps=10 --dream_ratio=5
```

This will:
- Download the MRPC dataset (automatically)
- Train the model for a few steps with warm-up
- Output results to `data/results/`
- Save logs to `data/logs/`

### Expected Output

After completion, you should see:
- `data/results/comparison_report.json`: Comparison with baseline
- `data/logs/training.log`: Structured training logs
- Console output with phase transitions (Wake/Dream)

### Verifying Results

Run the validation script to ensure everything is working:

```bash
python scripts/validate_quickstart.py
```

This script checks:
- Directory structure
- Dependency installation
- Data loader functionality
- Model loading
- Metrics computation
- End-to-end minimal training run

## Advanced Usage

### Temperature Sensitivity Analysis

To study the effect of temperature on dream phase performance:

```bash
python main.py --temperature_sweep --temperatures=0.5,0.7,0.9 --seeds_per_temp=5
```

This runs 15 experiments (3 temperatures × 5 seeds) and generates:
- `data/results/variance_report.json`: Variance metrics across temperatures

### Custom Configuration

Edit `config.py` to adjust:
- `MASK_RATE`: Masking probability for dream phase (default: 0.15)
- `WARMUP_STEPS`: Steps before dream phase starts (default: 10)
- `DREAM_RATIO`: Wake steps per dream step (default: 5)
- `ENTROPY_THRESHOLD`: Low-entropy detection threshold (default: 0.5)

### Resource Limits

The pipeline enforces strict resource limits for CI compatibility:
- Maximum wall-clock time: 5.5 hours
- Maximum memory: 8GB RAM
- CPU-only execution (no GPU)

If limits are exceeded, the training will abort and save a checkpoint.

## Troubleshooting

### "RuntimeError: Checksum mismatch"
The dataset download failed integrity verification. Delete the cached dataset
in `data/raw/` and retry.

### "MemoryLimitExceeded"
Reduce batch size in `config.py` or use a smaller dataset subset.

### "DataIntegrityError"
The downloaded dataset failed SHA-256 verification. Clear `data/raw/` and retry.

### Import Errors
Ensure you're running from the project root and that `code/` is in your Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/code"
```

## Next Steps

1. **Read the full specification**: `specs/001-dream-state-learning-implementing-rem-li/spec.md`
2. **Review the implementation plan**: `specs/001-dream-state-learning-implementing-rem-li/plan.md`
3. **Run the full pipeline**: Execute all user stories in sequence
4. **Analyze results**: Check `data/results/comparison_report.json` and `data/results/variance_report.json`

## Support

For issues or questions:
1. Check `data/logs/` for detailed error logs
2. Review the validation report from `scripts/validate_quickstart.py`
3. Ensure all prerequisites are met

## Research Context

This work explores whether REM-like consolidation cycles can improve language model
training. The implementation uses a Denoising Autoencoder (DAE) on masked real data
for the dream phase, rather than generative replay. This architectural choice was
made to ensure computational feasibility while preserving the core hypothesis.

Key references:
- Biological sleep consolidation: Walker & Stickgold (2006)
- Denoising autoencoders: Vincent et al. (2008)
- BERT masking strategy: Devlin et al. (2019)