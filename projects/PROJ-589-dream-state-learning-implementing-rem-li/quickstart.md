# Quickstart Guide: Dream-State Learning

## 1. Setup

Ensure you have Python 3.9+ installed.

```bash
# Navigate to the code directory
cd code

# Install dependencies
pip install -r requirements.txt
```

## 2. Running a Single Experiment

To run a quick test of the Wake/Dream cycle on a small subset:

```bash
python main.py --seed 42 --max-steps 100 --dataset glue/sst2
```

**Expected Output**:
- Logs in `data/logs/` showing "Wake Phase" and "Dream Phase" transitions.
- Checkpoint saved to `data/checkpoints/`.
- Final accuracy printed to stdout.

## 3. Running the Full Comparative Analysis

This runs the experimental model (Wake/Dream) and a baseline model (Continuous SFT) across 5 seeds, then performs a Wilcoxon signed-rank test.

```bash
python main.py --mode full_comparison
```

**Output**:
- `data/results/comparison_report.json`: Contains accuracy per seed, mean accuracy, and the Wilcoxon p-value.
- Console output: Summary of statistical significance.

## 4. Sensitivity Analysis

To verify robustness across temperature settings (0.5, 0.7, 0.9):

```bash
python main.py --mode temperature_sweep
```

**Output**:
- `data/results/sensitivity_report.json`: Variance in accuracy across temperatures.

## 5. Verifying Resource Constraints

The pipeline is designed to run within GitHub Actions free-tier limits (CPU, 7GB RAM, 6h).

To verify feasibility locally (dry-run):

```bash
./scripts/verify_feasibility.sh
```

## 6. Troubleshooting

- **DataIntegrityError**: Check your internet connection. The script requires downloading real GLUE data. If the issue persists, verify your network allows access to HuggingFace.
- **MemoryLimitExceeded**: Reduce the batch size in `config.py` or close other memory-intensive applications.
- **TimeLimitExceeded**: The process ran longer than 5 hours. This is expected for full runs; ensure you have sufficient time or reduce `--max-steps` for testing.

## 7. Understanding the Logs

Logs are structured JSON files in `data/logs/`. Key fields:
- `phase`: "WAKE" or "DREAM".
- `step`: Current training step.
- `entropy`: Output entropy (bits).
- `warmup_active`: Boolean indicating if warm-up is in progress.
- `memory_rss_kb`: Current memory usage.

Example log entry:
```json
{"timestamp": "2026-01-01T12:00:00Z", "phase": "DREAM", "step": 15, "entropy": 0.62, "warmup_active": false, "memory_rss_kb": 4500000}
```
