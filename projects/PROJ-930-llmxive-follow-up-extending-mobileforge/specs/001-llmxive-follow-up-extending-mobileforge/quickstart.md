# Quickstart: MobileForge Logic Distillation

## Prerequisites
- Python 3.11+  
- Git  
- Linux environment (local VM or GitHub Actions runner)  
- Internet access (only to fetch required Python packages; **no open MobileForge data is currently available**)  

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
# MobileForge log source URL would be set here once an open source becomes available
# export MOBILEFORGE_LOGS_URL="..."
```

## Execution Workflow

### Step 0: Bootstrap & Directory Creation
```bash
python code/bootstrap.py
# Confirms that all required directories exist, including code/models/
```

### Step 1: Install & Verify Dependencies
```bash
pip install -r code/requirements.txt
# CI will capture the install log.
```

### Step 2: Data Download & Validation (FR‑001)
```bash
# Placeholder – requires MobileForge logs
python code/pipeline/download.py
# Expected to place raw logs in data/raw/
python code/pipeline/extract.py
# Generates outputs/train_split.parquet, outputs/test_split.parquet, outputs/extraction_meta.json
```

> **Important**: At present there is **no publicly available MobileForge log dataset**. The pipeline cannot proceed until such data are provided. This limitation is intentional and flagged for specification revision.

### Step 3: Power Analysis (FR‑007)
```bash
python code/utils/power_analysis.py
# Writes outputs/power_analysis.json
```

### Step 4: Model Training (FR‑002, SC‑003)
```bash
# Quick sanity check (optional)
python code/pipeline/train.py --pilot

# Full training (will abort if >6 h)
python code/pipeline/train.py
# Model saved to code/models/distilled_distilbert/
```

### Step 5: Evaluation & Paired t‑Test (FR‑003‑005)
```bash
python code/pipeline/evaluate.py
# Generates outputs/evaluation_results.json (contains metrics, statistical_test, power_analysis, sensitivity_report, ablation_report)
```

### Step 6: Sensitivity Sweep (FR‑006)
*Performed automatically inside the evaluation script; results are embedded in `outputs/evaluation_results.json`.*

### Step 7: Hint‑Specific Ablation (Constitution VII)
```bash
python code/pipeline/evaluate.py --mode ablation
# Ablation results are embedded in the same `outputs/evaluation_results.json`.
```

### Step 8: Verification
```bash
pytest tests/
# Runs unit, integration, and contract tests.
```

## Troubleshooting
- **Missing MobileForge logs**: The pipeline pauses at Step 2 until an open log source is supplied.  
- **Training exceeds 6 h**: Watchdog will kill the process; reduce `--max-epochs` or the training subset size.  
- **CUDA detected**: Ensure `CUDA_VISIBLE_DEVICES=""` or run on a pure‑CPU runner.  
- **Checksum mismatch**: Re‑run Step 2; the download script will re‑download the corrupted file.  

---


