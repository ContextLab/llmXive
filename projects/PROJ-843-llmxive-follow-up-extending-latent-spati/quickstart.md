# llmXive Quickstart Guide

This guide describes how to run the full research pipeline for the "Latent Spatial Memory for Video World Models" extension.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`

## Running the Pipeline

The pipeline is executed via `code/main.py`. You can run specific phases or the entire workflow.

### Full Execution

To run the entire pipeline (Data Preparation -> Feature Extraction -> Geometry -> Evaluation):

## 1️⃣ Prepare data & download resources
```bash
cd code
python main.py --phase all
```

### Individual Phases

- **Dense Baseline (T016b)** (Downloads the pre-computed dense baseline, or generates it with MiDaS on CPU if the official source is unavailable):
 ```bash
 python code/data/dense_baseline.py
 ```
 *This step ensures `data/raw/dense_baseline_frames.npy` (and its provenance sidecar `data/raw/dense_baseline_provenance.json`) is created.*

- **Data Preparation** (Downloads baseline and RE10K, stratifies):
 ```bash
 python main.py --phase data_prepare
 ```
 *This phase ensures `data/raw/dense_baseline_frames.npy` is created.*

- **Feature Extraction** (Extracts SIFT/ORB):
 ```bash
 python main.py --phase extract_features
 ```

- **Geometry** (Solves epipolar, warps, aggregates):
 ```bash
 python main.py --phase compute_geometry
 ```

- **Evaluation** (Computes metrics, ANOVA, report):
 ```bash
 python main.py --phase evaluate
 ```

## Expected Artifacts

Upon successful completion, the following files should exist:

- `data/raw/dense_baseline_frames.npy` (Dense baseline depth maps)
- `data/raw/dense_baseline_provenance.json` (Source, checksum and model provenance for the baseline)
- `data/stratified/` (Stratified sequence folders)
- `data/features/` (Sparse feature files)
- `data/results/sparse_warped_frames.npy` (Aggregated warped frames)
- `data/results/metrics.json` (Final metrics)
- `data/results/hypothesis_verification.md` (Final report)

## Troubleshooting

- **Missing `dense_baseline_frames.npy`**: Run `python code/data/dense_baseline.py` directly. It attempts to download from HuggingFace and falls back to MiDaS generation on real frames (CPU only).
- **Import Errors**: Ensure you are running from the project root or `code/` directory and `requirements.txt` is installed.