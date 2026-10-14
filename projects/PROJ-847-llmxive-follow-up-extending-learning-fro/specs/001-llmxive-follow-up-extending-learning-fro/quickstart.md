# Quickstart: llmxive-density-analysis

## Prerequisites
```bash
# Clone the repository (already done in CI)
git clone https://github.com/your-org/llmxive-project.git
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
python src/llmxive/data.py --download
```

2. **Run fixed‑density baselines (with replication)**
```bash
python -m src.llmxive.cli.run_experiments \
    --mode fixed \
    --rhos 0.1 0.3 0.5 0.7 0.9 \
    --seeds 42 43 44 45 46 \
    --output outputs/fixed_baselines.json
```

3. **Run adaptive scheduler (with replication)**
```bash
python -m src.llmxive.cli.run_experiments \
    --mode adaptive \
    --seeds 42 43 44 45 46 \
    --output outputs/adaptive_run.json
```

4. **Statistical validation**
```bash
python -m src.llmxive.analysis \
    --fixed outputs/fixed_baselines.json \
    --adaptive outputs/adaptive_run.json \
    --outdir outputs/statistics
```

5. **Inspect results**
- Tables: `outputs/fixed_baselines.json`, `outputs/adaptive_run.json`
- Statistics: `outputs/statistics/paired_t_test.json`, `quadratic_fit.json`, `sensitivity_analysis.json`
- Plots: `outputs/figures/*.png`

All commands respect the defined wall‑clock limit; the trainer will auto‑checkpoint and exit gracefully if the limit is reached.

