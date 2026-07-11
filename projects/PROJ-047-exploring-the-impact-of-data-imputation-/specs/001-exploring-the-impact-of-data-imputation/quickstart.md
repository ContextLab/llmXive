# Quickstart: Exploring the Impact of Data Imputation Methods on Causal Inference

## Prerequisites

- Python 3.11+
- Git
- (Optional) Docker for isolated local testing

## Installation

1. **Clone the repository** (or navigate to the project root):
   ```bash
   cd projects/PROJ-047-exploring-the-impact-of-data-imputation-
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Simulation

### Full Simulation (200 Runs)

To execute the full sensitivity analysis across all MNAR parameters:

```bash
python code/analysis/run_simulation.py --runs 200 --beta-sweep 0.0,0.2,0.5,0.8,1.0
```

**Expected Output**:
- `data/results/simulation_summary.csv`
- `data/results/verification_stats.json`
- Console logs indicating progress and any convergence warnings.

### Single Run (Debugging)

To test a single run with specific parameters:

```bash
python code/analysis/run_simulation.py --runs 1 --beta 0.5 --seed 42
```

### Generating Figures

After the simulation completes, generate the required plots:

```bash
python code/analysis/visualization.py --input data/results/simulation_summary.csv
```

**Output Files**:
- `data/results/figures/bias_vs_beta.png`
- `data/results/figures/coverage_vs_beta.png`
- `data/results/figures/bias_distributions.png`

## Verification

### Check Ground Truth Integrity

Verify that the generated ground truth matches the theoretical value:

```bash
python code/tests/test_generate.py
```

### Run Statistical Tests

Verify the monotonicity and coverage collapse:

```bash
python code/analysis/sensitivity.py --input data/results/simulation_summary.csv
```

**Expected Output**:
- Spearman $\rho > 0.9$ for bias vs. $\beta$.
- Negative slope ($p < 0.05$) for coverage vs. $\beta$.

## Troubleshooting

- **Memory Error**: Reduce `--runs` or `sample_size` in `run_simulation.py`.
- **MICE Convergence Failure**: Increase `max_iter` in `impute.py` or exclude failed runs from bias averages.
- **Non-Monotonic Trend**: Check if $\beta$ values are too sparse; consider increasing the sweep density.
