# Quickstart: MobileForge Logic Distillation

## Prerequisites
- Python 3.11+  
- Git  
- Linux environment (local VM or GitHub Actions runner)  
- Internet access (to fetch Python packages and, if available, MobileForge logs)

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
# Provide MobileForge logs when they become available:
# export MOBILEFORGE_LOGS_URL=""
```

## Execution Workflow

### Step 0: Reproducibility Checklist
```bash
bash scripts/check_reproducibility.sh
# Verifies seeds, artifact hashes, and that a full re‑run yields identical success rates (≤ 1 % variance).
```

### Step 1: Data Download & Validation (FR‑001)
```bash
# Abort if MOBILEFORGE_LOGS_URL is unset
python code/pipeline/download_mobileforge.py

# Validate that all hints are purely linguistic
python code/utils/validate.py
# On success you will see "Validation passed: zero flagged hints."
```

> **Important**: If no MobileForge logs are provided, the pipeline stops here with a clear error. An optional demonstration using the public ExtractionDataset parquet can be run (see Step 2) but does **not** replace the required logs.

### Step 2: Optional Demonstration with Public ExtractionDataset
```bash
python code/pipeline/extract.py \
  --source https://huggingface.co/datasets/OSTShushack/ExtractionDataset/resolve/main/data/test-00000-of-00001.parquet \
  --output-dir outputs/
```

### Step 3: Power Analysis (FR‑007)
```bash
python code/utils/power_analysis.py
# Writes outputs/power_analysis.json
```

### Step 4: Model Training (FR‑002, SC‑003)
```bash
# Quick sanity check (optional)
python code/pipeline/train.py --pilot

# Full training (will abort if >6 h or if CUDA is detected)
python code/pipeline/train.py
# Model checkpoint saved to code/models/distilled_distilbert/
```

### Step 5: Pilot Evaluation (CI Feasibility Check)
```bash
# Runs the full evaluation pipeline on a reduced set of tasks (multiple runs each)
python code/pipeline/evaluate.py --mode pilot
# Generates outputs/pilot_evaluation.json
```

### Step 6: Full Offline Evaluation (FR‑003‑005)
*Run on a dedicated compute node (outside CI). The same command works locally:*
```bash
python code/pipeline/evaluate.py --mode standard
# Generates outputs/evaluation_results.json (primary McNemar + supplemental t‑test)
```

### Step 7: Sensitivity Sweep
*Performed automatically inside `evaluate.py`; results are embedded in `evaluation_results.json`.*

### Step 8: Hint‑Specific Ablation (Constitution VII, SC‑007)
```bash
python code/pipeline/evaluate.py --mode ablation
# Ablation results merged into the same evaluation_results.json; must achieve p < 0.05 (McNemar).
```

### Step 9: Verification
```bash
pytest tests/
# Runs unit, integration, and contract tests (including JSON‑Schema validation).
```

## Troubleshooting
- **Missing MobileForge logs**: Step 1 aborts with a clear message. Provide a valid `MOBILEFORGE_LOGS_URL` or wait for a spec revision.  
- **Training exceeds 6 h**: Watchdog will kill the process; reduce `--max-epochs` or the training subset size.  
- **CUDA detected**: Ensure `CUDA_VISIBLE_DEVICES=""` or run on a pure‑CPU runner.  
- **Checksum mismatch**: Re‑run the download step; the script will re‑download corrupted files.  
