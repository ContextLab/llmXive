# Quickstart: Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems

## Prerequisites

- Python 3.11+
- `pip` or `venv`
- Access to the verified datasets (requires internet connection for SNAP/Network Repository download).

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *(Note: `requirements.txt` contains pinned versions of `networkx`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `pytest`, `requests`, and other dependencies)*

## Running the Pipeline

The entire workflow can be executed with a single command:

```bash
python -m src.main --config config.yaml
```

This command will:

1. Load the configuration from `config.yaml`.
2. Download the required network datasets from verified SNAP sources (if not already present).
3. Compute topological metrics (degree distribution, clustering coefficient, average path length) for each network.
4. Run the Kuramoto synchronization simulations to find critical coupling strength.
5. Perform regression analysis linking topology to synchronization robustness.
6. Generate visualizations and summary reports.

### Expected Output Files

After successful execution, the following files will be created:

- **`results/sim_results.json`** – JSON array containing the synchronization threshold and metrics for each processed network.
- **`results/regression_summary.json`** – Summary of the linear/polynomial regression analysis (R², coefficients, p-values, significant predictors, VIF remediation).
- **`results/cv_report.json`** – Cross-validation metrics (mean R², std R², stability flags).
- **`results/verification_report.json`** – Manual verification log for the first 5 networks (alphabetically sorted).
- **`results/manual_verification_log.csv`** – CSV with network IDs, thresholds, and verification metadata.
- **`results/pipeline_status.json`** – Execution status (`SUCCESS` or `TIMEOUT`) with timing information.
- **`results/heatmap_thresholds.png`** – Heatmap visualizing the relationship between topological predictors and synchronization thresholds.
- **`results/comparison_plot.png`** – Bar chart of regression coefficients with error bars.
- **`results/model_comparison_plot.png`** – Side-by-side plot of R² values for primary and secondary models (if applicable).
- **`data/processed/metrics_*.json`** – Per-network topological metrics (one file per input graph).
- **`data/checksums.txt`** – SHA-256 checksums of all downloaded raw network files.

## Verification

To ensure the implementation matches the specification:

### 1. Unit Tests
```bash
pytest tests/ -v
```
This validates topology metrics, Kuramoto RK45 integration, regression logic, and cross-validation.

### 2. Schema Validation
The pipeline automatically validates output JSONs against the schemas defined in `contracts/`.
```bash
python -m src.validators --validate-all
```

### 3. Manual Verification (SC-003)
Check `results/verification_report.json` and `results/manual_verification_log.csv` for an initial set of alphabetically sorted networks (first 5). Verify that the synchronization thresholds match those in `results/sim_results.json`.

### 4. Ring Graph Validation (SC-006)
The test suite includes `test_ring_graph_analytical_match_pct` which constructs a ring graph (N=200) and verifies the Kuramoto synchronization threshold is within 5% of the known analytical value. [UNRESOLVED-CLAIM: c_2e5e0d22 — status=not_enough_info]
```bash
pytest tests/test_simulation.py::test_ring_graph_analytical_match_pct -v
```

### 5. ANOVA Test (SC-001)
After regression, check `results/anova_report.json` to confirm that the ANOVA p-value is < 0.05, validating the overall model significance.

## Troubleshooting

- **Timeout Error**: If the pipeline exceeds 6 hours, check `results/pipeline_status.json`. The system will log the specific network ID causing the delay and mark the status as `TIMEOUT`.
- **Insufficient Data**: If fewer than 10 networks are available, the regression step will be skipped, and `results/descriptive_stats.json` will be generated instead with a warning message.
- **Disconnected Graphs**: Networks with multiple disconnected components will be flagged in `results/sim_results.json` with `status: "disconnected"`, `coupling_strength_threshold: null`, and excluded from regression.
- **Data Fetch Failure**: If SNAP or Network Repository URLs fail, the pipeline will halt with a clear error message (no silent fallback to synthetic data).
- **Multicollinearity**: If VIF > 5 is detected during regression, the system will either remove the highest-VIF predictor and re-fit, or fall back to Ridge regression (α=1.0). The action taken is recorded in `results/regression_summary.json`.

## Pipeline Phases

The pipeline executes in the following order:

1. **Phase 0 – Configuration**: Load `config.yaml` and validate paths.
2. **Phase 1 – Data Availability**: Count raw network files; if < 10, write warning and skip regression.
3. **Phase 2 – Metric Computation** (US-1): For each network, compute topological metrics and save per-network JSON.
4. **Phase 3 – Kuramoto Simulation** (US-1): For each network, run synchronization simulation via K-sweep/bisection to find critical coupling.
5. **Phase 4 – Aggregation**: Combine all per-network results into `results/sim_results.json`.
6. **Phase 5 – Regression Analysis** (US-2): Fit linear and polynomial models; check VIF; perform ANOVA.
7. **Phase 6 – Cross-Validation** (US-2): Execute conditional CV (LOOCV for N<50, 10-fold for N≥50); generate `cv_report.json`.
8. **Phase 7 – Visualization** (US-3): Generate heatmaps and comparison plots.
9. **Phase 8 – Verification** (SC-003): Generate manual verification report for the first 5 networks.
10. **Phase 9 – Status**: Write `results/pipeline_status.json` with SUCCESS or TIMEOUT.

## Key Parameters

- **Synchronization Threshold**: r(t) > 0.8 sustained for t > 100 time units.
- **Coupling Strength Range**: K ∈ [0, 5] (bisection search or discrete sweep).
- **Kuramoto Integration**: RK45 method with rtol=1e-6, atol=1e-9.
- **Oscillator Count**: N = 200 per network.
- **VIF Threshold**: 5.0 (multicollinearity flag).
- **Regression R² Threshold**: > 0.6 (required by SC-001).
- **ANOVA p-value Threshold**: < 0.05 (statistical significance).
- **Cross-Validation**: LOOCV if dataset size < 50; 10-fold CV if ≥ 50.
- **Cross-Validation Stability**: std(R²) < 0.1 (robustness flag).

## Example: Running a Single Network

To process a single network manually (for testing or debugging):

```bash
python -c "
from src.topology import compute_metrics
from src.simulation import process_single_network
import networkx as nx
from pathlib import Path

# Load or create a test network
G = nx.karate_club_graph()

# Compute metrics
metrics = compute_metrics(G, 'test_network')
print(f'Metrics: {metrics}')

# Run simulation
result = process_single_network(G, 'test_network')
print(f'Synchronization threshold: {result.coupling_strength_threshold}')
"
```

## Next Steps

After the pipeline completes successfully:

1. Review `results/regression_summary.json` for key statistics (R², p-values, significant predictors).
2. Inspect the visualization files (PNG) in `results/` for heatmaps and comparison plots.
3. Check `results/verification_report.json` for manual verification status.
4. If the pipeline times out, identify the bottleneck network in `results/pipeline_status.json` and consider optimizing its simulation parameters.
5. If regression is skipped due to insufficient data, review `results/descriptive_stats.json` for summary statistics.

## Support & Documentation

- **API Documentation**: See `docs/api_topology.md`, `docs/api_simulation.md`, and `docs/api_stats.md` for detailed function signatures.
- **Configuration**: Edit `config.yaml` to adjust thresholds, paths, and random seeds.
- **Testing**: Run `pytest tests/ -v` to validate all components.
- **Logs**: Check `logs/` directory for detailed execution logs (if logging is enabled in config).
