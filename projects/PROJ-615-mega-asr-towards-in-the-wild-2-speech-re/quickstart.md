# Quickstart: Mega-ASR Scaled Benchmark

This guide runs a scaled-down version of the Mega-ASR robustness benchmark. It uses a small subset of real audio data and a lightweight ASR model to compute WER/CER across different acoustic distortions.

## Prerequisites
Ensure you are in the project root directory.

## Run the Benchmark

Execute the following command. It will automatically detect if a GPU is available (using `whisper-base` if so, `whisper-tiny` otherwise) and generate the output artifacts.

```bash
python code/run_benchmark.py
```

## Expected Outputs
After execution, the following files will be generated:
- `data/results.csv`: Detailed per-record metrics.
- `data/benchmark_summary.json`: Aggregated error rates by acoustic category.
- `figures/wer_by_category.png`: Visualization of the results.

These artifacts demonstrate the "acoustic robustness bottleneck" by showing higher error rates in distorted categories (e.g., `noise`, `mixed`, `far_field`) compared to clean scenarios.
