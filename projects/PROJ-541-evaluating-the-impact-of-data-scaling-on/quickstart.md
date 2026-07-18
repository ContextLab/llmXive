# Quick Start Guide: Evaluating Data Scaling Impact

## Prerequisites

- Python 3.11+
- pip
- At least 14GB disk space (for real-world datasets)
- CPU-only environment (GPU disabled by default)

## Step 1: Setup

```bash
# Clone and enter directory
git clone <repo-url>
cd llmXive

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r code/requirements.txt
```

## Step 2: Run Synthetic Data Pipeline

Execute the full simulation and analysis:

```bash
python code/main.py --mode synthetic
```

**Expected Outputs:**
- `results/simulation_results.csv`
- `results/mixed_effects_synthetic.csv`
- `results/figures/error_rate_plot.png`

**What it does:**
1. Generates synthetic data with known ground truth (null and alternative hypotheses).
2. Applies Standardization, Min-Max, and Robust scaling.
3. Runs t-tests, ANOVA, and Chi-squared tests.
4. Aggregates Type I error rates and Power.
5. Fits mixed-effects models to analyze scaling impact.

## Step 3: Run Real-World Data Pipeline

```bash
python code/main.py --mode real-world
```

**Expected Outputs:**
- `data/metadata/manifest.json`
- `results/mixed_effects_summary.csv`
- `results/comparison_report.csv`

**What it does:**
1. Downloads datasets from UCI/OpenML (as listed in `data/config/datasets.yaml`).
2. Cleans and preprocesses data.
3. Applies scaling and runs tests.
4. Generates comparison reports.

## Step 4: Verify Results

### Check Simulation Results
```bash
head results/simulation_results.csv
```

### View Plots
Open `results/figures/error_rate_plot.png` in any image viewer.

### Run Tests
```bash
# Unit tests
pytest code/tests/unit/ -v

# Integration tests
pytest code/tests/integration/ -v
```

## Troubleshooting

- **Dataset Download Failed**: Ensure internet connectivity. Check `data/config/datasets.yaml` for valid dataset IDs.
- **Memory Error**: Reduce `n_iterations` in `data/config/simulation.yaml` or use a smaller sample size.
- **Import Errors**: Verify `code/requirements.txt` is installed correctly.

## Next Steps

- Modify `data/config/simulation.yaml` to explore different distributional properties.
- Add new datasets to `data/config/datasets.yaml` for real-world validation.
- Extend `code/visualization/plots.py` to generate additional visualizations.