# Quickstart: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Prerequisites

- Python 3.10+
- Git
- Docker (if running fMRIPrep locally; CI uses a containerized version)
- ~ GB free disk space (for temporary data)
- **Note**: fMRIPrep requires >7 GB RAM. Run preprocessing steps on a local machine or cloud instance, not on the CI runner.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-232-investigating-the-relationship-between-b
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

### 1. Data Availability Check
Before running the full pipeline, verify that the required data (BMRQ, fMRI) is present in OpenNeuro ds000233.

```bash
python src/data/download.py --check-only
```
*Output*: A JSON report listing available subjects and variables. If BMRQ is missing, the pipeline will halt and generate a Data Gap Report.

### 2. Preprocessing (Off-CI)
**Warning**: This step requires >7 GB RAM and is **not** designed for the CI runner. Run this locally or on a cloud instance.

```bash
python src/data/preprocess.py --subjects 50 --mode cpu
```

### 3. Connectivity & Metrics
Extract connectivity matrices and compute graph metrics (with VIF check).

```bash
python src/analysis/connectivity.py --subjects 50
python src/analysis/graph_metrics.py --subjects 50
```

### 4. Statistical Analysis
Run partial correlations, power analysis, and regression.

```bash
python src/analysis/stats.py --output results/analysis_results.csv
```

### 5. Visualization
Generate scatter plots and network diagrams.

```bash
python src/analysis/visualize.py --input results/analysis_results.csv
```

## Testing

Run the unit and integration tests to verify the pipeline integrity.

```bash
pytest tests/ -v
```

## Troubleshooting

- **Memory Error**: If `fMRIPrep` fails due to RAM, reduce the number of subjects or run on a machine with >16 GB RAM. **Do not run fMRIPrep on the CI runner for N>1.**
- **Data Missing**: If the script reports "BMRQ not found", the dataset does not contain the required behavioral scores. The study cannot proceed with the primary hypothesis. A Data Gap Report will be generated.
- **Collinearity**: If VIF > 5 is reported, the pipeline will automatically apply PCA or remove predictors. Check `results/vif_report.json` for details.
- **Timeout**: If the CI job times out, the pipeline is designed to process a small subset (N=1) for validation. Full runs require a local machine or cloud instance.