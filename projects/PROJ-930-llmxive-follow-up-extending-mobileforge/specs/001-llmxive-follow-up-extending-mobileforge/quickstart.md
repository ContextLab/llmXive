# Quickstart: MobileForge Logic Distillation

## 1. Prerequisites
- Python 3.11+
- Git
- Access to a Linux environment (GitHub Actions or local Linux VM)
- Sufficient free disk space is required.

## 2. Setup

### 2.1 Clone and Install
```bash
git clone <repo-url>
cd projects/930-llmxive-follow-up-extending-mobileforge/code/
pip install -r requirements.txt
```

### 2.2 Environment Configuration
Set the following environment variables in `.env` or your shell:
```bash
export DATASET_URL="" # Verified source
export RANDOM_SEED=42
export EVAL_TASKS_N=500 # Will be overwritten by power_analysis output
```

## 3. Execution Workflow

### Step 1: Power Analysis (FR-007)
Run the power analysis to determine the required sample size.
```bash
python utils/power_analysis.py
# Output: state/validated_n.json
```
*Note: This step includes a pilot run to estimate baseline success rate (p0).*

### Step 2: Data Extraction & Filtering (FR-001)
Extract and filter the dataset.
```bash
python pipeline/extract.py
# Output: data/processed/train_splits.parquet, data/processed/test_splits.parquet
```

### Step 3: Feasibility Pilot & Training (FR-002, FR-008)
Run a feasibility pilot (a small sample set) then full training.
```bash
python pipeline/train.py --pilot # Validates CPU feasibility
python pipeline/train.py # Full training
# Output: models/distilled_t5/
```
*Note: This script includes a check to abort if CUDA is detected.*

### Step 4: Evaluation & Statistical Validation (FR-003, FR-005)
Run evaluation against the baseline and perform McNemar's test.
```bash
python pipeline/evaluate.py
# Output: state/evaluation_results.json
```

### Step 5: Sensitivity & Ablation (FR-006, Constitution VII)
Run sensitivity sweep and ablation study.
```bash
python pipeline/evaluate.py --mode sensitivity
python pipeline/evaluate.py --mode ablation
```

## 4. Verification
Run the test suite to ensure all contracts are met.
```bash
pytest tests/
```

## 5. Troubleshooting
- **CUDA Detected**: If training fails with a CUDA error, ensure `CUDA_VISIBLE_DEVICES=""` is set.
- **Memory Error**: Reduce batch size in `pipeline/train.py`.
- **Missing Data**: Ensure `DATASET_URL` is accessible and the file is not corrupted.
- **Power Analysis Fallback**: If pilot data is unavailable, the script defaults to p0=0.5.