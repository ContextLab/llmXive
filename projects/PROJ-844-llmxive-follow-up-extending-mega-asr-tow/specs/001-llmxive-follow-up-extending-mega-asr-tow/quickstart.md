# Quickstart: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## Prerequisites

- Python 3.11+
- Git
- Sufficient RAM (for running the full pipeline)
- Sufficient Disk Space (for dataset downloads and derived artifacts)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

4. **Verify environment**:
   ```bash
   python -c "import torch; import transformers; import sklearn; import pygam; print('OK')"
   ```

## Running the Pipeline

The main orchestration script is `code/main.py`.

### Step 1: Download and Prepare Data
```bash
python code/main.py --action download --dataset caiman --output data/raw/
```
*This downloads the verified `CAIMAN-ASR-BackgroundNoise` dataset, filters for SNR > 20dB, and performs a pre-flight check for transcripts.*

### Step 2: Generate Stress Curves
```bash
python code/main.py --action stress --clip-limit 500 --models whisper-tiny,whisper-base --output data/derived/stress_curves.parquet
```
*This applies a set of distortion vectors to 500 clips and computes SSS/WER.*

### Step 3: Human Annotation (Manual Step)
*This step requires manual intervention. A subset of stress curves is presented to human annotators.*
```bash
# The pipeline will generate a sample file for annotation at data/derived/sample_for_annotation.csv
# After annotation, the results are saved to data/derived/human_annotations.csv
# For CI/CD verification, a small 'gold standard' subset (pre-annotated) is used instead of mock data.
```

### Step 4: Identify Collapse Points
```bash
python code/main.py --action collapse --threshold 0.5 --wer-multiplier 2.0 --human-data data/derived/human_annotations.csv --input data/derived/stress_curves.parquet --output data/derived/collapse_points.parquet
```
*This identifies the specific intensity where semantic collapse occurs, using human annotations as ground truth.*

### Step 5: Train Regression Model
```bash
python code/main.py --action regress --input data/derived/collapse_points.parquet --output data/derived/regression_results.json
```
*This trains the GAM model to predict collapse and outputs the "critical interaction vector".*

### Step 6: Sensitivity Analysis
```bash
python code/main.py --action sensitivity --input data/derived/collapse_points.parquet --output data/derived/sensitivity_report.json
```
*This sweeps the threshold across a moderate range (0.40-0.60) and reports the variance in the interaction vector.*

### Step 7: Run Tests
```bash
pytest tests/unit/ -v
```

## Expected Outputs

- `data/derived/stress_curves.parquet`: A substantial volume of stress test data.
- `data/derived/human_annotations.csv`: A subset of human annotations (A small proportion of stress curves).
- `data/derived/collapse_points.parquet`: A substantial set of collapse thresholds.
- `data/derived/regression_results.json`: Coefficients and R² scores.
- `data/derived/sensitivity_report.json`: Variance report for sensitivity analysis.

## Troubleshooting

- **OOM Error**: Reduce `--clip-limit` in the stress step.
- **CUDA Error**: The pipeline is CPU-first. If a model tries to load CUDA, ensure `device="cpu"` is set in `code/utils/metrics.py`.
- **Dataset Not Found**: Verify the URL in `code/utils/data_loader.py` matches the verified list in `research.md`.
- **Human Data Missing**: The `collapse` action will fail if `human_annotations.csv` is not present. Ensure the manual annotation step is completed.
