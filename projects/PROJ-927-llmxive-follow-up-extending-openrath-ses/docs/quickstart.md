# Quick Start Guide

This guide walks you through running the llmXive pipeline from scratch.

## Step 1: Environment Setup

Ensure you have Python 3.11+ installed.

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-927-llmxive-follow-up-extending-openrath-ses

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Initialize Structure

Create the necessary directory structure (if not already present):

```bash
python code/setup_structure.py
```

## Step 3: Run a Single Workflow Test

To verify the system works with a small dataset:

```bash
python code/main.py --seed 42 --count 5
```

This will:
1. Generate 5 workflows.
2. Execute them through both architectures.
3. Inject corruption (default 10%).
4. Reconstruct states and calculate metrics.
5. Output results to `data/processed/results/`.

## Step 4: Run Full Sensitivity Sweep

To run the full evaluation across corruption rates:

```bash
python code/main.py --sweep
```

This iterates over `{0.05, 0.10, 0.20}` and aggregates results.

## Step 5: Verify Results

Check the aggregated metrics:

```bash
cat data/processed/results/aggregated_metrics.json
```

Verify the project state and checksums:

```bash
cat state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml
```

## Troubleshooting

### Missing Directories
If you get `FileNotFoundError`, ensure you ran `setup_structure.py`.

### Checksum Mismatch
If the state file reports a checksum mismatch, re-run the checksum utility:
```bash
python -c "from utils.checksum_manager import update_artifact_hashes; update_artifact_hashes()"
```

### Execution Timeout
If the process times out, use `--resume` to continue from the last completed workflow.
