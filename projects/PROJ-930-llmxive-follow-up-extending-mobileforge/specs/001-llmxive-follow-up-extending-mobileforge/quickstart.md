# Quickstart: MobileForge Logic Distillation

## 1. Prerequisites
- Python 3.11+  
- Git  
- Linux environment (local VM or GitHub Actions runner)  
- Internet access to download the two open datasets

## 2. Setup

```bash
# Clone the repository
git clone <repo-url>
cd projects/930-llmxive-follow-up-extending-mobileforge

# Install pinned dependencies
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file or export manually:

```bash
export RANDOM_SEED=42
export DATASET_URL="https://huggingface.co/datasets/OSTShushack/ExtractionDataset"
export ANDROIDWORLD_URL="https://huggingface.co/datasets/google-deepmind/androidworld"
```

## 3. Execution Workflow

### Step 0: Verify Bootstrap Artifacts
```bash
# Ensure required bootstrap files exist (requirements.txt, pyproject.toml, .ruff.toml)
python -c "import pathlib, sys; missing = [p for p in ['requirements.txt','pyproject.toml','.ruff.toml'] if not pathlib.Path(p).exists()]; 
sys.exit(1) if missing else print('Bootstrap files present.')"
```

### Step 1: Verify Data Availability
```bash
python code/utils/check_data.py   # checks downloads & checksums
```

### Step 2: Power Analysis (FR‑007)
```bash
python code/utils/power_analysis.py   # writes state/validated_n.json
# The script aborts if it cannot write the file; training will not start without it.
```

### Step 3: Data Extraction (FR‑001)
```bash
python code/pipeline/extract.py
# Outputs: data/processed/train_splits.parquet, data/processed/test_splits.parquet
```

### Step 4: Feasibility Pilot & Full Training (FR‑002, SC‑003)
```bash
# Pilot (quick sanity check)
python code/pipeline/train.py --pilot

# Full training (will fail if >6 h)
python code/pipeline/train.py
# Model saved to models/distilled_t5/
```

### Step 5: Evaluation & Statistical Test (FR‑003‑005)
```bash
python code/pipeline/evaluate.py
# Generates state/evaluation_results.json
```

### Step 6: Sensitivity Sweep (FR‑006)
```bash
python code/pipeline/evaluate.py --mode sensitivity
```

### Step 7: Hint‑Specific Ablation (Constitution VII)
```bash
python code/pipeline/evaluate.py --mode ablation
```

### Step 8: Verification
```bash
pytest tests/   # runs unit, integration, and contract tests
```

## 4. Troubleshooting
- **Training exceeds 6 h**: The watchdog will kill the process and CI will report a failure. Reduce `--max-epochs` or the sample size.  
- **CUDA detected**: Ensure `CUDA_VISIBLE_DEVICES=""` or run on a pure‑CPU runner.  
- **Checksum mismatch**: Re‑run Step 1; the script will re‑download the corrupted file.  
- **Power analysis missing**: Verify `state/validated_n.json` exists; rerun Step 2.

---


