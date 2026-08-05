# Quick Start Guide: Dream-State Learning

This guide provides step-by-step instructions to run the Dream-State Learning pipeline on a small GLUE subset.

## Prerequisites

- Python 3.8+
- 7GB+ available RAM
- Internet connection for dataset download
- ~2 hours for a full run (depending on dataset size)

## Step 1: Setup Environment

```bash
# Clone and navigate to project
git clone <repository-url>
cd PROJ-589-dream-state-learning-implementing-rem-li

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Step 2: Verify Project Structure

Ensure all required directories exist:
```bash
python code/setup_structure.py
```

Expected output:
```
[INFO] Verifying project structure...
[INFO] All required directories exist.
```

## Step 3: Run a Single Training Experiment

Run a minimal experiment on the SST-2 subset:

```bash
python code/main.py \
 --seed 42 \
 --dataset glue-sst2 \
 --epochs 1 \
 --max-steps 50 \
 --output-dir data/results
```

### Expected Output

The script will:
1. Download the GLUE-SST2 dataset (with checksum verification)
2. Initialize a DistilBERT model
3. Run 50 training steps with alternating Wake/Dream phases
4. Log phase transitions, entropy metrics, and warm-up status
5. Save the final model checkpoint to `data/checkpoints/`
6. Output evaluation metrics to `data/results/`

### Sample Log Output

```
[INFO] Starting training run with seed 42
[INFO] Dataset: glue-sst2, Steps: 50
[INFO] Warm-up: Steps 0-9 (no dream phase)
[EVENT] Step 10: Phase transition Wake -> Dream
[METRIC] Entropy: 1.23 bits (threshold: 0.5)
[EVENT] Step 11: Dream phase - DAE reconstruction
[METRIC] Dream loss: 0.456
[EVENT] Step 12: Phase transition Dream -> Wake
...
[INFO] Training complete. Checkpoint saved.
[INFO] Evaluation: Accuracy=0.82, F1=0.79
```

## Step 4: Run Temperature Sensitivity Analysis

To test robustness across different temperature values:

```bash
python code/main.py \
 --temperature-sweep \
 --temps 0.5,0.7,0.9 \
 --dataset glue-sst2 \
 --epochs 1 \
 --max-steps 20
```

This will:
1. Run the full pipeline for each temperature value
2. Collect final accuracy for each run
3. Compute variance using scikit-learn's `var` function
4. Generate a sensitivity report at `data/results/sensitivity_report.json`

## Step 5: Run Baseline Comparison

Compare the Dream-State model against a continuous fine-tuning baseline:

```bash
python code/main.py \
 --baseline \
 --dataset glue-sst2 \
 --epochs 1 \
 --max-steps 50 \
 --compare
```

This will:
1. Run the experimental (Wake/Dream) pipeline
2. Run the baseline (continuous SFT) pipeline with identical token count
3. Perform Wilcoxon signed-rank test across 5 seeds
4. Save comparison report to `data/results/comparison_report.json`

## Step 6: Verify Resource Constraints

Ensure the pipeline runs within GitHub Actions limits:

```bash
bash code/scripts/verify_feasibility.sh
```

This script will:
1. Run a dry-run with 5-hour time limit
2. Monitor memory usage (7GB limit)
3. Abort and save checkpoint if limits are exceeded
4. Report success/failure status

## Troubleshooting

### OOM Errors
If you encounter Out-Of-Memory errors:
- Reduce `max-steps` in the command
- Use a smaller dataset subset
- Check `data/logs/memory_monitor.log` for peak usage

### Dataset Download Failures
If dataset download fails:
- Verify internet connection
- Check that `datasets` library is installed
- Ensure sufficient disk space in `data/raw/`

### Checksum Mismatch
If you see `DataIntegrityError`:
- Delete the corrupted dataset in `data/raw/`
- Re-run the script to re-download

## Next Steps

- Review `docs/README.md` for detailed architecture documentation
- Read `specs/001-dream-state-learning-implementing-rem-li/spec.md` for user stories
- Run `pytest tests/` to execute the full test suite
- Explore `data/results/` for evaluation outputs
