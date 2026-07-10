# Quickstart: Exploring the Impact of Data Imputation Methods on Causal Inference

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with 7GB+ RAM).

## Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   git clone <repo-url>
   cd projects/PROJ-047-exploring-the-impact-of-data-imputation-
   ```

2. **Create a virtual environment** and install dependencies.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

## Running the Simulation

### Step 1: Generate Data (Single Replication Test)
Run a single replication to verify the data generation pipeline.
```bash
python code/generate_data.py --seed 42 --beta 0.5 --n 1000
```
*Output*: `data/raw/synthetic_seed_42_beta_0.5.csv`

### Step 2: Run Full Simulation (200 Replications)
Execute the full pipeline (Generation → Imputation → Estimation → Analysis).
```bash
python code/run_simulation.py --replications 200 --seeds 1-200 --betas 0.1,0.5,1.0,2.0
```
*Output*:
- `data/raw/` (200 files)
- `data/processed/` (Imputed files)
- `data/results/estimates.csv`
- `data/results/anova_results.json`
- `data/results/sensitivity_plot.png`

### Step 3: Verify Results
Check the ANOVA results to see if methods differ significantly.
```bash
cat data/results/anova_results.json
```
*Expected*: A JSON object containing `f_statistic` and `p_value`. If `p_value < 0.05`, the methods are significantly different.

## Testing

Run the unit tests to ensure data generation and imputation logic is correct.
```bash
pytest tests/
```

## Troubleshooting

- **MICE Convergence Failure**: If the pipeline logs "MICE failed to converge", check `data/processed/` for the specific seed. The script will exclude this replication from the ANOVA but log the event.
- **Memory Error**: Ensure you are not running the full 200 replications on a machine with <7GB RAM. The script is optimized for the GitHub Actions free tier.
