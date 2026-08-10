# Training Module

This directory contains the core training infrastructure for the llmXive project.

## Components

- `train_loop.py`: Core training and evaluation loops for both autoregressive and diffusion models.
- `callbacks.py`: Logging and monitoring callbacks for training metrics.
- `run_experiment.py`: Orchestrates multi-seed experiments and aggregates results.

## Usage

Experiments are typically launched via `run_experiment.py`:

```bash
python code/training/run_experiment.py --config config.yaml
```

## Dependencies

This module relies on:
- `torch` for model execution
- `utils.config` for hyperparameters
- `utils.logging` for logging infrastructure
- `utils.monitor` for resource tracking
