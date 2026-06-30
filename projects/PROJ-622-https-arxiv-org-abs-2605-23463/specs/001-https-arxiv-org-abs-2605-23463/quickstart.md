# StepAudio 2.5 CPU Adaptation Quickstart

This guide runs the simplified, CPU-tractable version of the StepAudio 2.5 pipeline.
It generates synthetic data and trains a tiny proxy model to demonstrate the core logic.

## Prerequisites

Ensure you have a standard Python 3 environment with `numpy` and `matplotlib` installed.
No GPU, ffmpeg, or heavy transformers are required.

```bash
pip install numpy matplotlib
```

## Run Commands

Execute the following commands in order. Each step produces artifacts for the next.

```bash
python code/prepare_cpu.py --output-dir data/synthetic_wenet --num-samples 100
python code/train_cpu_proxy.py --data-dir data/synthetic_wenet --output-dir data/results --epochs 10
```

## Expected Outputs

After running, verify the following files exist in the `data/` directory:

- `data/synthetic_wenet/text`: List of synthetic transcripts.
- `data/synthetic_wenet/metadata.json`: Metadata for generated segments.
- `data/results/results.csv`: Training metrics (loss, accuracy).
- `data/results/training_curve.png`: Visualization of training progress.
