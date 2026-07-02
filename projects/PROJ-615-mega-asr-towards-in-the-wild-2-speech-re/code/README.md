# Mega-ASR Adaptation: Scaled Robustness Benchmark

## Purpose
This adaptation reproduces the **core quantitative claim** of the Mega-ASR paper: robustness against real-world acoustic distortions (noise, echo, far-field, etc.).

## Approximations & Scaling
The original paper trains a massive model on 2M samples and reports WER on full benchmarks. To fit the CPU/CI constraints (or a single free Kaggle GPU), we apply the following scaling:

1.  **Model Substitution**: We do **not** train Mega-ASR. Instead, we use a **small, pre-trained Whisper-tiny** (CPU-tractable) or **Whisper-base** (GPU-offload) as the baseline. The "Mega-ASR" improvement is simulated by applying the paper's core logic: **Acoustic-to-Semantic Progressive Supervision** is approximated by **dynamic prompt engineering** based on detected distortion types (a lightweight proxy for the learned policy).
    *   *Note*: If running on CPU, we use `Whisper-tiny`. If the execution stage detects a GPU requirement (or if you force GPU), we use `Whisper-base` with `load_in_8bit` to fit VRAM.
2.  **Dataset Subsampling**: We subsample the `data/examples.jsonl` to the first **20 records** (mix of categories) to ensure rapid execution.
3.  **Metric**: We compute **Word Error Rate (WER)** for English samples and **Character Error Rate (CER)** for Chinese samples, exactly as defined in the paper's `error_rate.py`.
4.  **Distortion Analysis**: We group results by the `subset` or `source_scenes` to demonstrate the "robustness bottleneck" (higher error on mixed/distorted scenarios).

## Output Artifacts
- `data/results.csv`: Per-record error rates (WER/CER) and category breakdown.
- `data/benchmark_summary.json`: Aggregate WER/CER by distortion category (Noise, Echo, Mixed, etc.).
- `figures/wer_by_category.png`: A bar chart visualizing the error rates across acoustic conditions.

## Execution
Run `quickstart.md` to generate these artifacts. The script handles both CPU (default) and GPU (offload) paths gracefully.
