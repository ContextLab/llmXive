# Quickstart: Pipeline Validation - Investigating the Impact of Network Topology on Neural Entrainment (Simulated Data)

## Prerequisites

* Python 3.11+
* pip

## Installation

1. **Clone and Setup**:
   ```bash
   cd projects/PROJ-486-investigating-the-impact-of-network-topo
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Data Download & Synthetic Generation**:
   ```bash
   python code/download.py
   ```
   *The script will attempt to download the HCP connectivity parquet. If the required entrainment column is missing (as is the case for all verified external datasets), it will automatically generate synthetic entrainment values using a fixed random seed (42) and a modest linear relationship (`r≈0.3`) with the primary topology metric. All generated data are tagged `data_source: "synthetic"`.*

## Execution

Run the full pipeline:
```bash
python code/main.py
```

This will:
1. Load and validate data.
2. Compute Clustering Coefficient and Path Length for Schaefer, AAL, and Power264 atlases.
3. Perform **Partial Correlation** (controlling for the other metric) and Bonferroni correction.
4. Generate visualizations (`artifacts/plots/`):
   * `scatter_schaefer.png` – primary scatter with 95 % CI.
   * `robustness_bar.png` – bar chart of absolute effect‑size differences (y‑axis: **Absolute Difference in Effect Size (|r|)**) for AAL and Power264 versus Schaefer.
5. Output `data/processed/results.csv` and a summary report (`artifacts/reports/summary.txt`) that includes explicit warnings about synthetic data, power, and collinearity.

## Troubleshooting

* **"Invalid Entrainment Data"**: The input CSV lacks `subject_id` or `metric_value`. Ensure the generated synthetic file exists or provide a real CSV with those columns.
* **"Power Warning: N < 30"**: Fewer than 30 subjects survived the inner join. Results are exploratory.
* **"Collinearity Warning: VIF > 5"**: Clustering and Path Length are highly correlated; the pipeline proceeds with **Partial Correlation** to isolate unique effects.
* **"Synthetic Data Used"**: All results are labeled with `data_source: "synthetic"`; the pipeline validates code, not the biological hypothesis.