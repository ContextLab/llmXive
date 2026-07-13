# Quickstart: Assessing the Sensitivity of Common Statistical Tests to Dataset Size

## Prerequisites

- Python 3.11+
- `pip` (package manager)
- Git (for cloning the repository)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-482-assessing-the-sensitivity-of-common-stat
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

### Full Simulation
To run the complete Monte Carlo study (all sample sizes, distributions, and tests):
```bash
python code/main.py --full
```
This will:
1. Generate synthetic data for all configurations.
2. Run adaptive Monte Carlo simulations using **Clopper-Pearson** intervals for convergence.
3. Aggregate results and compute confidence intervals.
4. Fit a **GLM binomial regression** on the error rates.
5. Generate visualizations.

### Single Configuration (Debug)
To test a single configuration (e.g., t-test, normal, n=50):
```bash
python code/main.py --config "sample_size=50,distribution=normal,test=ttest,effect=0.0"
```

## Output Locations

- **Raw Data**: `data/raw/simulation_runs.csv`
- **Aggregated Metrics**: `data/processed/error_metrics.csv`
- **Regression Results**: `data/processed/regression_results.csv`
- **Visualizations**: `data/processed/plots/` (PNG/SVG files)

## Verification

To verify the simulation engine:
```bash
pytest tests/unit/test_data_generator.py
pytest tests/unit/test_simulation.py
```
These tests ensure that:
- Generated data matches theoretical parameters.
- Type I error rates for normal data (n=50) are close to 0.05.
- Confidence intervals are calculated using the **Clopper-Pearson** method.

## Troubleshooting

- **Memory Error**: Reduce the maximum replicate count in `code/config.py` (default a sufficiently large number).
- **Convergence Warning**: If CI width > 0.01 after max replicates, the result is flagged in the CSV. Check `convergence_achieved` column.
- **Fisher's Exact**: If `test_used` is `fisher_exact`, the system automatically switched due to small cell counts (expected count < 5).