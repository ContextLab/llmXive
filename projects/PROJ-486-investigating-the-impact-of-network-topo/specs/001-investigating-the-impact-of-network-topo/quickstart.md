# Quickstart: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

## Prerequisites

- Python 3.11+
- `pip`
- Substantial RAM (recommended for smooth execution, though a lower baseline is minimum)
- GB+ Disk Space

## Installation

1. **Clone the repository** (or navigate to the feature branch):
   ```bash
   git checkout 001-network-topology-entrainment
   cd projects/PROJ-486-investigating-the-impact-of-network-topo/code
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` will pin versions for `pandas`, `numpy`, `networkx`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`.*

## Running the Pipeline

### Option 1: Default Simulation (No Input Data)
If no external data is provided, the system automatically generates synthetic data and runs the analysis.

```bash
python main.py --mode simulation
```

### Option 2: With External Entrainment Data
Provide a CSV with `subject_id` and `entrainment_metric`. The system will attempt to join with HCP topology data (if available) or fall back to simulation if N < 30.

```bash
python main.py --input data/external_entrainment.csv --mode hybrid
```

### Option 3: Sensitivity Analysis (All Atlases)
Run the analysis across Schaefer, AAL, and Power 264 atlases to generate the comparative bar chart.

```bash
python main.py --atlases schaefer aal power --mode simulation
```

## Expected Outputs

1. **`data/analysis_results.csv`**: Detailed statistical output per subject and per atlas.
2. **`data/scatter_plot.png`**: Relationship between topology and entrainment (with 95% CI).
3. **`data/sensitivity_bar_chart.png`**: Comparative bar chart showing absolute difference in effect sizes for AAL and Power vs. Schaefer.
4. **`data/report.txt`**: Summary of findings, including power warnings and collinearity flags.

## Troubleshooting

- **"Invalid Entrainment Data"**: Ensure the input CSV has columns `subject_id` and `entrainment_metric` with numeric values.
- **"Power Warning: N < 30"**: The system has automatically switched to simulation mode. Check logs for the simulated dataset details.
- **"Collinearity Warning"**: The VIF for one or more predictors exceeded the commonly accepted threshold for multicollinearity. Individual p-values are suppressed; refer to the joint R-squared in the report.
