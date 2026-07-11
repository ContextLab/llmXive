# Quickstart: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Prerequisites

- Python 3.11+
- Access to UCF101, Kinetics, or DAVIS datasets (via `ucimlrepo`, HuggingFace `datasets`, or manual download).
- **AnyFlow Model Weights**: You must provide the frozen AnyFlow model in ONNX format locally. (No verified public URL exists).
- Sufficient RAM available (for CI/Local run).

## Installation

1.  **Clone and Setup Environment**:
    ```bash
    cd projects/PROJ-812-llmxive-follow-up-extending-anyflow-any/code
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `ucimlrepo` and `datasets` for correct dataset loading.*

2.  **Prepare Data**:
    - Ensure video clips are downloaded to `data/raw/videos/`.
    - Ensure the AnyFlow ONNX model is placed in `models/anyflow_cpu.onnx`.

## Execution Steps

### Step 1: Data Curation (Manual Annotation)
Run the annotation script to generate the ground truth CSV.
```bash
python data_curation/download_clips.py --source ucf101 --count 200 --output data/raw/videos/
python data_curation/annotate.py --input data/raw/videos/ --output data/raw/annotations.csv
```
*Note: This step requires human interaction. Review each clip and assign a score 0.0–1.0. A subset of clips will be double-annotated for reliability (Krippendorff's Alpha).*

### Step 2: Metric Calculation
Run the divergence computation pipeline.
```bash
python metric_calculation/compute_divergence.py \
    --model models/anyflow_cpu.onnx \
    --videos data/raw/videos/ \
    --annotations data/raw/annotations.csv \
    --output data/processed/divergence_metrics.csv
```
*This step will take several hours on CPU. It processes short-frame clips, computes optical flow variance, and runs the mandatory Quantization Sensitivity Test.*

### Step 3: Statistical Analysis
Run the correlation and sensitivity analysis.
```bash
python analysis/distribution.py \
    --annotations data/raw/annotations.csv \
    --output data/processed/score_distribution.json

python analysis/correlation.py \
    --annotations data/raw/annotations.csv \
    --metrics data/processed/divergence_metrics.csv \
    --output data/processed/correlation_results.json

python analysis/sensitivity.py \
    --metrics data/processed/divergence_metrics.csv \
    --thresholds 0.01,0.05,0.1 \
    --output data/processed/sensitivity_report.json

python analysis/report.py \
    --correlation data/processed/correlation_results.json \
    --sensitivity data/processed/sensitivity_report.json \
    --distribution data/processed/score_distribution.json \
    --output data/processed/final_report.json
```

## Expected Outputs

- `data/processed/final_report.json`: Contains Pearson $r$, Spearman $\rho$, p-values, sensitivity rates, score distribution, and explicit **Runtime Environment** statement ("CPU-only").
- Console output: Summary of the associational relationship.

## Troubleshooting

- **CUDA Error**: Ensure `onnxruntime` is installed with CPU support only. Check `providers=['CPUExecutionProvider']`.
- **Memory Error**: Reduce batch size in `compute_divergence.py` or process fewer clips.
- **Missing Model**: Verify `models/anyflow_cpu.onnx` exists. The system cannot proceed without it.
- **Annotation Reliability**: If Krippendorff's Alpha < 0.6, review the annotation rubric and re-annotate.
- **Model Architecture Mismatch**: If the model hash or structure does not match the "On-Policy Flow Map Distil" definition, the script will halt with an error.