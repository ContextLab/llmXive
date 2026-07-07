# Quick Start Guide

## Setup
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Ensure Python 3.10+ is installed.

## Running the Pipeline
Execute the following command:
```bash
bash run.sh
```

## Expected Artifacts
After running the pipeline, you should see the following files:
- `data/raw/human_eval_data.jsonl`
- `data/processed/energy_results_raw.csv`
- `data/processed/energy_results_aggregated.csv`
- `figures/energy_bar.png`
- `figures/tradeoff_scatter.png`

## Troubleshooting
- If `human_eval` is not found, install it: `pip install human-eval`.
- If OOM errors occur, ensure you have enough RAM (StarCoder-1B requires ~2GB+).