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

# Install exact dependencies (requirements are under code/)
pip install -r code/requirements.txt
```

### Environment Variables
Create a `.env` file or export manually:

```bash
export RANDOM_SEED=42
export EXTRACTION_DATA_URL="https://huggingface.co/datasets/OSTShushack/ExtractionDataset"
export ANDROIDWORLD_URL="https://huggingface.co/datasets/google-deepmind/androidworld"
```

## Execution Workflow

### Step 0: Verify Bootstrap
```bash
python -c "import pathlib, sys; missing = [p for p in ['code/requirements.txt','code/.ruff.toml','pyproject.toml'] if not pathlib.Path(p).exists()]; sys.exit(1) if missing else print('Bootstrap files present.')"
```

### Step 1: Install & Verify Dependencies
```bash
pip install -r code/requirements.txt
# Verify install succeeded (exit code 0). CI will capture the log.
```

### Step 2: Power Analysis (FR‑007)
```bash
python code/utils/power_analysis.py   # writes outputs/power_analysis.json
# The script aborts if it cannot write the file.
```

### Step 3: Data Extraction (FR‑001)
```bash
python code/pipeline/extract.py
# Outputs: outputs/train_split.parquet, outputs/test_split.parquet, outputs/extraction_meta.json
```

### Step 4: Model Training (FR‑002, SC‑003)
```bash
# Pilot run (quick sanity check)
python code/pipeline/train.py --pilot

# Full training (will fail if >6 h)
python code/pipeline/train.py
# Model saved to outputs/distilled_t5/
```

### Step 5: Evaluation & McNemar Test (FR‑003‑005)
```bash
python code/pipeline/evaluate.py
# Generates outputs/evaluation_results.json
```

### Step 6: Sensitivity Sweep (FR‑006)
```bash
python code/pipeline/evaluate.py --mode sensitivity
# Generates outputs/sensitivity_report.json
```

### Step 7: Hint‑Specific Ablation (Constitution VII)
```bash
python code/pipeline/evaluate.py --mode ablation
# Generates outputs/ablation_report.json
```

### Step 8: Verification
```bash
pytest tests/   # runs unit, integration, and contract tests
```

## Troubleshooting
- **Training exceeds 6 h**: The watchdog will kill the process and CI will report failure. Reduce `--max-epochs` or the sample size.  
- **CUDA detected**: Ensure `CUDA_VISIBLE_DEVICES=""` or run on a pure‑CPU runner.  
- **Checksum mismatch**: Re‑run Step 1; the script will re‑download the corrupted file.  
- **Power analysis missing**: Verify `outputs/power_analysis.json` exists; rerun Step 2.  

---

