# Quickstart: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

## 1. Prerequisites

- Python 3.11+
- Git
- Access to the verified HCP datasets (see `research.md`).

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-486-investigating-the-impact-of-network-topo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Preparation

### Step 1: Download HCP Data
The pipeline expects connectivity data in `data/raw/`.
```bash
# Example: Download the verified HCP dataset (adjust URL if needed)
python code/data_loader.py --download-hcp --output data/raw/hcp_subset.csv
```
*Note: If the verified URL does not contain connectivity matrices, the script will halt with a clear error.*

### Step 2: Prepare Entrainment Data
Create `data/raw/entrainment_metrics.csv` with the following columns:
- `subject_id`
- `entrainment_metric`

```csv
subject_id,entrainment_metric
100307,0.45
100408,0.52
...
```

### Step 3: (Optional) Validation Mode
To test the pipeline logic without real data:
```bash
python code/main.py --validation-mode --target-r 0.5
```

## 4. Running the Analysis

### Empirical Mode (Real Data)
```bash
python code/main.py --atlas Schaefer
```
This will:
1. Load HCP and entrainment data.
2. Check N >= 30. If not, halt with "Data Insufficient".
3. Compute topology metrics.
4. Run correlations and MLR (if applicable).
5. Generate visualizations.

### Sensitivity Analysis
```bash
python code/main.py --atlas all
```
This runs the analysis for Schaefer, AAL, and Power 264 and generates the comparative bar chart.

## 5. Output

- **Results**: `data/processed/correlation_results.csv`
- **Flags**: `data/processed/metric_flags.json`
- **Visualizations**:
  - `data/visualizations/scatter_topology_entrainment.png`
  - `data/visualizations/atlas_comparison_bar.png`

## 6. Troubleshooting

- **"Data Insufficient"**: The inner join of HCP and entrainment data yielded N < 30. Provide more data or accept the exploratory status.
- **"Invalid Entrainment Data"**: The input CSV is missing `subject_id` or `entrainment_metric`, or contains non-numeric values.
- **"Collinearity Warning"**: VIF > 5 for predictors. MLR coefficients are suppressed; only univariate results are reported.
