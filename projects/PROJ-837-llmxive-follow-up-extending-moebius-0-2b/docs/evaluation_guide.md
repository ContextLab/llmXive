# Evaluation Guide: Chunked Processing for Memory Constraints

## Overview
This document describes the evaluation pipeline for the Moebius Dynamic Inpainting model,
specifically focusing on the memory-optimized processing required to run FID and LPIPS
metrics within the 7GB RAM limit of the CI environment.

## Key Components

### 1. `code/eval/metrics.py`
Contains the core logic for:
- `InpaintingEvalDataset`: Loads images and masks from disk.
- `evaluate_model`: Orchestrates the chunked evaluation loop.
- `compute_fid` / `compute_lpips`: Calculation utilities.

**Memory Strategy**:
The `evaluate_model` function processes data in batches defined by `chunk_size`.
It uses `torchmetrics` to accumulate statistics incrementally, avoiding the need to
store all features in memory simultaneously.

### 2. `code/eval/chunked_runner.py`
A safety wrapper that:
- Detects available RAM at runtime using `psutil`.
- Estimates memory usage based on model size and batch size.
- Automatically reduces `chunk_size` if an OutOfMemory (OOM) error is detected.
- Ensures the evaluation completes even on low-resource machines.

## Usage

### Running Evaluation
To run the evaluation with automatic memory management:

```bash
python code/eval/chunked_runner.py \
 --model data/results/model_weights.pt \
 --dataset data/processed/masked_images \
 --annotations data/annotations/scores.csv \
 --output data/results/evaluation_report.json \
 --initial-chunk 8
```

### Manual Chunk Size
If you know your system's capacity, you can run directly:
```bash
python code/eval/metrics.py \
 --model data/results/model_weights.pt \
 --dataset data/processed/masked_images \
 --annotations data/annotations/scores.csv \
 --output data/results/metrics.json \
 --chunk-size 4
```

## Troubleshooting

- **OOM Errors**: If you encounter OOM errors, the `chunked_runner.py` will automatically
 reduce the batch size. If it fails at `chunk_size=1`, the model or dataset is too large
 for the available hardware.
- **Slow Performance**: Reducing `chunk_size` increases overhead. If memory allows, increase
 the `--initial-chunk` value for better throughput.
- **FID/LPIPS Values**: Ensure the dataset is pre-processed correctly (images normalized to [0, 1]).

## CI vs Research Mode
The evaluation logic is mode-agnostic. However, in CI mode, the `chunked_runner` is
strictly enforced to guarantee reproducibility across different CI runners with varying RAM.
In Research mode, users may opt for larger batch sizes if local hardware permits.
