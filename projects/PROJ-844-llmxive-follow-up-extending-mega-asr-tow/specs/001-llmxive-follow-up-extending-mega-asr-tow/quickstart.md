# Quickstart: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## Prerequisites

- Python 3.11+  
- ≤ 7 GB RAM, 14 GB disk (GitHub Actions free tier)  
- Internet access (for Hugging Face datasets)  
- Optional: Kaggle account (for GPU escape hatch – not required)

## Installation

```bash
# Clone repository
git clone <repo-url>
cd <project-dir>

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r code/requirements.txt
```

## Configuration

1. Set random seeds in `code/utils/config.py`:
   ```python
   import random, numpy as np, torch
   SEED = 42
   random.seed(SEED)
   np.random.seed(SEED)
   torch.manual_seed(SEED)
   ```
2. Verify dataset availability:
   ```bash
   python code/data/download.py --check
   ```

## Running the Pipeline (CPU‑first)

### Step 1: Download & Stratify Data
```bash
python code/data/preprocess.py \
  --dataset ami,librispeech \
  --split test,test.clean \
  --output data/raw/stratified.parquet
```
- Uses AMI test and LibriSpeech test.clean.
- Generates synthetic RIRs for every clip to create `simulated_rt60` and `simulated_room_volume` strata.

### Step 2: Generate Distortion Stress Curves
```bash
python code/distortion/generator.py \
  --input data/raw/stratified.parquet \
  --output data/derived/stress_curves.parquet \
  --snr-range -10 30 \
  --rt60-range 0.1 1.0 \
  --models whisper-tiny
```
- Generates 54 distortion scenarios per clip (9 SNR × 6 RT60).  
- Batch size = 100 to stay within RAM limits.

### Step 3: Compute Collapse Intensities
```bash
python code/metrics/collapse.py \
  --input data/derived/stress_curves.parquet \
  --output data/derived/collapse_points.parquet
```
- Applies smoothing, derivative analysis, **morphology check**, and deterministic interpolation (FR‑021).  
- Handles empty hypotheses, noise floor, and non-monotonic curves.

### Step 4: Train Regression Model
```bash
python code/analysis/regression.py \
  --input data/derived/collapse_points.parquet \
  --output data/derived/critical_vectors.parquet
```
- Hierarchical regression with interaction terms, SHAP analysis, and FDR correction.

### Step 5: Sensitivity Analysis
```bash
python code/analysis/validation.py \
  --input data/derived/collapse_points.parquet \
  --output data/derived/sensitivity_results.parquet
```

### Step 6: Domain Validation Pilot (FR-011)
```bash
python code/validation/pilot.py \
  --dataset ami \
  --rt60-threshold 0.5 \
  --sample-size 100 \
  --output data/derived/validation_pilot.parquet
```
- Annotates N=100 high-reverb clips and validates SSS.

### Step 7: Realism Validation (FR-018)
```bash
python code/validation/realism.py \
  --dataset dns-challenge \
  --sample-size 50 \
  --output data/derived/realism_validation.parquet
```
- Validates synthetic distortions against N=50 DNS Challenge clips.

## Verification

### Unit Tests
```bash
pytest tests/unit/ -v
```
- Ensure `tests/unit/__init__.py` exists and contains basic sanity checks.

### Contract Tests
```bash
pytest tests/contract/ -v
```
- Validates outputs against `contracts/*.schema.yaml`.

### Integration Tests
```bash
pytest tests/integration/ -v
```
- Runs the full pipeline on a tiny subset (e.g., 10 clips) to confirm end‑to‑end functionality.

## Output Artifacts

- `data/derived/stress_curves.parquet`: Stress‑curve records (SSS, WER, etc.).  
- `data/derived/collapse_points.parquet`: Collapse intensity records (per FR‑021).  
- `data/derived/critical_vectors.parquet`: Regression coefficients and interaction vector.  
- `data/derived/sensitivity_results.parquet`: Sensitivity analysis outcomes.
- `data/derived/validation_pilot.parquet`: Domain validation results.
- `data/derived/realism_validation.parquet`: Realism validation results.

## Troubleshooting

- **Out of Memory**: Reduce `--batch-size` in `generator.py`.  
- **Dataset Not Found**: Verify URLs in `code/data/download.py`.  
- **CUDA Error**: No GPU required; if accidentally invoked, the runner will offload to Kaggle GPU (scaled‑down) automatically.