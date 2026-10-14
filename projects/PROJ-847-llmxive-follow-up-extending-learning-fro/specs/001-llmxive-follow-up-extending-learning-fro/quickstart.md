# Quickstart: llmxive-density-analysis

## Prerequisites
```bash
# Clone the repository (already done in CI)
git clone
cd llmxive-project

# Create a fresh virtual environment
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Execution

1. **Download & preprocess data**
```bash
python code/data.py --download
```

2. **Run fixed‑density baselines (with replication)**
```bash
python -m code.run_experiments \
    --mode fixed \
    --rhos 0.1 0.3 0.5 0.7 0.9 \
    --seeds 42 43 44 \
    --output outputs/fixed_baselines.csv
```

3. **Run adaptive scheduler (with replication)**
```bash
python -m code.run_experiments \
    --mode adaptive \
    --seeds 42 43 44 \
    --output outputs/adaptive_run.json
```

4. **Statistical validation**
```bash
python -m code.analysis \
    --fixed outputs/fixed_baselines.csv \
    --adaptive outputs/adaptive_run.json \
    --outdir outputs/statistics
```

5. **Inspect results**
- Tables: `outputs/fixed_baselines.csv`, `outputs/adaptive_run.json`
- Statistics: `outputs/statistics/independent_t_test.json`, `quadratic_fit.json`, `sensitivity_analysis.json`
- Plots: `outputs/figures/*.png`

All commands respect the defined wall‑clock limit; the trainer will auto‑checkpoint and exit gracefully if the limit is reached.