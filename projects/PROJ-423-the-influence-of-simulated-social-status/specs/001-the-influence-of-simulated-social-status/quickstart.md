# Quickstart: The Influence of Simulated Social Status on Risk-Taking Behavior

## Prerequisites
- Python 3.11+
- Git
- Access to a terminal (Linux/macOS/WSL)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-423-the-influence-of-simulated-social-status
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline consists of three main steps: Data Generation, Analysis, and Reporting.

### Step 1: Generate Synthetic Data
This step creates the experimental dataset based on pre-registered meta-analytic effect sizes (N=800).
```bash
python code/generate_data.py
```
- **Output**: `data/raw/synthetic_data.csv`
- **Note**: This script uses a fixed random seed for reproducibility.

### Step 2: Preprocess Data
This step cleans the data, handles missing values, and prepares it for analysis.
```bash
python code/preprocess.py
```
- **Input**: `data/raw/synthetic_data.csv`
- **Output**: `data/processed/cleaned_data.csv`

### Step 3: Run Analysis & Sensitivity Check
This step fits the **Fixed-Effects Linear Model (ANOVA)**, calculates VIF, and runs the sensitivity sweep.
```bash
python code/analysis.py
```
- **Input**: `data/processed/cleaned_data.csv`
- **Output**:
  - `data/results/model_summary.json`
  - `data/results/sensitivity_analysis.csv`
  - `data/results/vif_report.json`

### Step 4: Generate Report
This step creates the forest plot and final HTML report.
```bash
python code/report.py
```
- **Input**: Model results from Step 3.
- **Output**:
  - `data/results/forest_plot.png`
  - `data/results/report.html`

## Verification

To verify the pipeline runs correctly on a fresh environment:

1.  **Check Data Integrity**:
    ```bash
    python -c "import json; print(json.load(open('data/checksums.json')))"
    ```
    Ensure checksums match the files in `data/raw/` and `data/processed/`.

2.  **Run Unit Tests**:
    ```bash
    pytest tests/unit/
    ```

3.  **Run Contract Tests**:
    ```bash
    pytest tests/contract/
    ```
    This validates that the output data matches the schemas defined in `contracts/`.

## Troubleshooting

- **Memory Error**: If the analysis fails due to memory constraints, reduce the `N` parameter in `code/generate_data.py` (e.g., `N=500`).
- **Missing Dependencies**: Ensure `statsmodels` and `scikit-learn` are installed.
- **Schema Validation Failure**: Check that `data/processed/cleaned_data.csv` has the correct column names and types as defined in `contracts/data.schema.yaml`.

## Next Steps
- Review the generated `report.html` for the forest plot and statistical summary.
- Examine `data/results/sensitivity_analysis.csv` to verify the stability of the interaction effect.
- Verify that the **Recovered Estimate** is within the 95% CI of the **Injected Parameter** (Parameter Recovery Study).
- Submit results for `research_review` stage.