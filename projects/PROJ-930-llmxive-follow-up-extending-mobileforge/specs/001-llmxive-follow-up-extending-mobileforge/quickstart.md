# Quickstart: MobileForge Logic Distillation

## Prerequisites
- Python 3.11+  
- Git  
- Linux environment (local VM or GitHub Actions runner)  
- Internet access to download the two open datasets  

## Setup

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-930-llmxive-follow-up-extending-mobileforge

# Install exact dependencies
pip install -r code/requirements.txt
```

### Environment Variables
Create a `.env` file or export manually:

```bash
export RANDOM_SEED=42
export EXTRACTION_DATA_URL="https://huggingface.co/datasets/mobileforge/mobileforge-logs"
export ANDROIDWORLD_URL="https://huggingface.co/datasets/google-deepmind/androidworld"
```

## Execution Workflow

### Step 0: Bootstrap & Directory Creation
```bash
python code/bootstrap.py
# Confirms that all required directories (code/models, code/data/raw, code/data/processed, code/tests/unit, code/tests/integration, data/raw, data/processed, etc.) exist.
```

### Step 1: Install & Verify Dependencies
```bash
pip install -r code/requirements.txt
# CI will capture the install log.
```

### Step 2: Download & Validate Extraction Dataset (FR‑001)
```bash
python code/pipeline/download.py
# → data/raw/mobileforge_logs.parquet
python code/utils/validate_extraction_dataset.py
# Exits 0 on success; any schema mismatch aborts.
```

### Step 3: Power Analysis (FR‑007)
```bash
python code/utils/power_analysis.py
# Writes outputs/power_analysis.json
```

### Step 4: Data Extraction & Splitting (FR‑001)
```bash
python code/pipeline/extract.py
# Generates outputs/train_split.parquet, outputs/test_split.parquet, outputs/extraction_meta.json
```

### Step 5: Model Training (FR‑002, SC‑003)
```bash
# Quick sanity check (optional)
python code/pipeline/train.py --pilot

# Full training (will abort if >6 h)
python code/pipeline/train.py
# Model saved to outputs/distilled_t5/
```

### Step 6: Evaluation & McNemar Test (FR‑003‑005)
```bash
python code/pipeline/evaluate.py
# Generates outputs/evaluation_results.json (contains metrics, statistical_test, power_analysis, sensitivity_report, ablation_report)
```

### Step 7: Sensitivity Sweep (FR‑006)
```bash
# Sensitivity sweep is performed automatically inside the evaluation script; results are embedded in outputs/evaluation_results.json.
```

### Step 8: Hint‑Specific Ablation (Constitution VII)
```bash
python code/pipeline/evaluate.py --mode ablation
# Ablation results are embedded in outputs/evaluation_results.json
```

### Step 9: Verification
```bash
pytest tests/
# Runs unit, integration, and contract tests.
```

## Troubleshooting
- **Training exceeds 6 h**: Watchdog will kill the process; reduce `--max-epochs` or the training subset size.  
- **CUDA detected**: Ensure `CUDA_VISIBLE_DEVICES=""` or run on a pure‑CPU runner.  
- **Checksum mismatch**: Re‑run Step 2; the download script will re‑download the corrupted file.  
- **Power analysis missing**: Verify `outputs/power_analysis.json` exists; rerun Step 3.  

---



