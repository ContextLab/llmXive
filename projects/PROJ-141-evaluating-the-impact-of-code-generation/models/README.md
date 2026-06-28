# Models Directory

Store pre-trained models and model checkpoints here.

## Model Requirements

All models must be:
- CPU-tractable (≤1GB size for JaCoText/StarCoder)
- Compatible with GitHub Actions free-tier (2 CPU, 7 GB RAM)
- Documented with verification in `code/models/`

## Model Files

- `jacotext_cpu.py`: Java code generation model wrapper
- `starcoder_cpu.py`: Python code generation model wrapper
- `model_selector.py`: Conditional model selection with fallback logic
