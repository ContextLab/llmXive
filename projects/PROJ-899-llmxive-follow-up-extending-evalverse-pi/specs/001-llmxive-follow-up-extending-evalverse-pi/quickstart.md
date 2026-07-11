# Quickstart: llmXive follow-up: extending "EvalVerse" with CPU-tractable Feature Distillation

## Prerequisites

- Python 3.11+
- Git
- Access to the EvalVerse dataset (manual download required)
- GitHub Actions runner (for CI testing)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llmxive-follow-up
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` pins all dependencies for reproducibility.*

4. **Download and verify the EvalVerse dataset**:
 - Since no verified public URL exists, you must manually download the EvalVerse dataset and place it in `data/raw/evalverse/`.
 - Ensure the directory structure matches:
 ```
 data/
 └── raw/
 └── evalverse/
 ├── clips/
 │ ├── clip_001.mp4
 │ └──...
 └── metadata.json
 ```
 - After placing the data, compute and record the SHA-256 checksum:
 ```bash
 python scripts/checksum_data.py data/raw/evalverse/
 ```
 This checksum will be recorded in `state/projects/.../artifact_hashes` for reproducibility and future verification (Principle II: Verified Accuracy).

## Running the Pipeline

### 1. Preliminary Validation (FR-009) — GATE STEP (Optional)
Run the validation step to confirm any optional VLM proxy (if present in EvalVerse metadata) is aligned with human experts.
```bash
python src/cli/run_pipeline.py --step validate
```
- **Output**: `reports/validation.json`
- **Expected**: `status: "valid"` if VLM Pearson r ≥ 0.70, `status: "invalid"` if r < 0.70, or `status: "no_vlm_available"` if VLM scores are not in the EvalVerse metadata.
- **If Invalid (r < 0.70)**: The VLM proxy cannot be used for secondary analyses. The main study proceeds with human expert scores only.
- **If Valid or No VLM**: Proceed to Step 2. The main study will use human expert scores as the target variable.
- **CRITICAL**: The main distillation study ALWAYS uses human expert scores as the target, regardless of the VLM validation outcome.

### 2. Feature Extraction
Extract low-level visual and audio features from all clips.
```bash
python src/cli/run_pipeline.py --step extract --batch-size 100
```
- **Output**: `data/processed/features.parquet`
- **Note**: Use `--batch-size` to control memory usage. The `profiles.py` module will populate `FeatureVector.memory_peak` during this step (FR-006).

### 3. Compute Dimension Correlation Matrix
Compute the correlation structure among target dimensions to inform multiple-comparison correction.
```bash
python src/cli/run_pipeline.py --step compute-dim-correlation
```
- **Output**: `data/processed/dimension_correlation_matrix.csv`
- **Note**: This step is required for permutation-based FWER control in Step 4.

### 4. Model Training & Evaluation (Against Human Expert Scores)
Train models and calculate correlations with **human expert ground truth**.
```bash
python src/cli/run_pipeline.py --step train --model ridge --baseline --threshold-sweep
```
- **Output**:
 - `data/processed/model_results.csv` (ModelPerformance records)
 - `reports/summary.md` (Final summary with classifications and flags)
- **Flags**:
 - `--baseline`: Computes Mean Predictor and Shuffled Features baselines with permutation tests.
 - `--threshold-sweep`: Enables the sensitivity analysis (FR-005).
- **Target Variable**: Human expert scores (the ground truth for cinematic quality).

### 5. Compute Profiling
Profile memory and time usage to verify GitHub Actions feasibility.
```bash
python src/cli/run_pipeline.py --step profile --clips 100
```
- **Output**: `reports/profiling.json`
- **Expected**: Peak memory < 7GB, inference time scales to fit N=10,000 within 6 hours.

## Testing

Run the unit and integration tests:
```bash
pytest tests/
```
- **Contract Tests**: Validate outputs against YAML schemas in `contracts/`.
- **Unit Tests**: Test feature extraction on synthetic video/audio data (generated on-the-fly).
- **Integration Tests**: Run the full pipeline on a small sample.

## Troubleshooting

- **Missing Audio Track**: The pipeline will log a warning and skip audio features. No crash.
- **Optical Flow Failure**: The pipeline will return a "zero-motion" vector and flag the clip as "low-quality."
- **Memory Error**: Reduce `--batch-size` or ensure the dataset is not loaded entirely into memory.
- **Time Limit Exceeded**: Use `--clips 1000` for a fast validation run before the full N=10,000 run.
- **Validation Fails (r < 0.70)**: The VLM proxy is invalid. The main study proceeds with human expert scores only. No study halt.
- **EvalVerse Checksum Mismatch**: The data may be corrupted or tampered with. Re-download and recompute the checksum.
