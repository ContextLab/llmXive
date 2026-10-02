# PROJ-483: Evaluating the Robustness of Common Statistical Tests to Non-Independence

## Executive Summary

This project investigates how violations of the independence assumption affect the Type I error rates and statistical power of t-tests, ANOVA, and Chi-squared tests. By simulating dependency structures (AR(1), Block Bootstrap, Spatial) on real public datasets (UCI Wine, Car Evaluation, Zoo), we quantify the extent to which these common tests become unreliable as non-independence increases.

## Key Findings (Expected)

- **Type I Error Inflation**: As dependency strength ($r$) increases, the observed Type I error rate for parametric tests (t-test, ANOVA) is expected to exceed the nominal $\alpha=0.05$.
- **Power Reduction**: The presence of dependency is expected to reduce the statistical power to detect true effects compared to the independent case.
- **Test Sensitivity**: Different tests (t-test vs. Chi-squared) and dependency structures (temporal vs. spatial) will exhibit varying degrees of robustness.

## Installation

```bash
git clone <repo-url>
cd PROJ-483-evaluating-the-robustness-of-common-stat
pip install -r requirements.txt
```

## Usage

### 1. Data Preparation

The pipeline automatically fetches real datasets from verified UCI URLs.

```bash
python code/run_data_loader.py
```

*Note: If a dataset fetch fails, the pipeline halts with a `DataFetchError`. No synthetic fallback is used.*

### 2. Running the Simulation

Execute the full Monte Carlo sweep:

```bash
python code/main.py
```

**Configuration**:
- Edit `code/config.yaml` to modify `n_replications`, `seed`, or `dependency_strengths`.
- Default: 10,000 replications, $r \in \{0.0, 0.1, 0.2, 0.3, 0.5\}$.

### 3. Results

Output artifacts are saved in `results/`:
- `aggregated_unified.csv`: Raw simulation data.
- `type1_error_table.md`: Summary table of error rates with Clopper-Pearson CIs.
- `power_analysis.csv`: Power reduction metrics.
- `figures/`: Visualizations of error rate curves and power loss.

### 4. Validation

Ensure reproducibility and integrity:

```bash
python code/validate_quickstart.py
```

## Project Structure

- `code/`: Core implementation (simulation, injection, metrics).
- `data/`: Raw datasets and manifests.
- `results/`: Simulation outputs and logs.
- `docs/`: Detailed documentation (Binning Strategy, Methodology).
- `tests/`: Unit and integration tests.

## Methodology

- **Null Hypothesis**: Constructed via "Generate-then-Inject" (synthetic) or "Inject-then-Permute" (real data).
- **Dependency Injection**: AR(1) for temporal, Block Bootstrap for hierarchical, Spatial Kernel for spatial.
- **Metrics**: Type I Error Rate, Power, Clopper-Pearson Confidence Intervals.

## Performance

Target: 10,000 replications in < 6 hours on 2-core/7GB RAM.
- Pre-flight memory checks prevent out-of-memory errors.
- Vectorized NumPy operations used for efficiency.

## Contributing

1. Ensure all tests pass (`pytest tests/ -v`).
2. Update `docs/` if methodology changes.
3. Verify real data fetches before committing.

## License

MIT License.
