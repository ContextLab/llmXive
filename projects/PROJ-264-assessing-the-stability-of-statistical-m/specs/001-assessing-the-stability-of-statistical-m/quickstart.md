# Quickstart: Assessing the Stability of Statistical Model Performance Across Data Subsets

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution) or a local environment with sufficient RAM.

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llmxive
 ```

2. **Set up the environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. **Install dependencies**:
 The project uses `pandas`, `numpy`, `scikit-learn`, `scipy`, and `requests`.
 ```bash
 # Ensure requirements.txt contains:
 # pandas>=2.0.0
 # numpy>=1.24.0
 # scikit-learn>=1.3.0
 # scipy>=1.11.0
 ```

## Dataset List

The following datasets are targeted for the analysis. **Note**: Datasets are loaded from verified OpenML IDs as defined in `research.md`. All listed datasets are binary classification tasks.

| Dataset Name | OpenML ID | Type | Note |
|:--- |:--- |:--- |:--- |
| Pima Indians Diabetes | 1590 | Binary Classification | Verified binary target. |
| Breast Cancer (Wisconsin) | 1510 | Binary Classification | Verified binary target. |
| Ionosphere | 1512 | Binary Classification | Verified binary target. |
| Sonar | 1513 | Binary Classification | Verified binary target. |
| Liver Disorders (Bupa) | 1514 | Binary Classification | Verified binary target. |
| Heart Disease (Cleveland) | 1520 | Binary Classification | Verified binary target. |
| German Credit | 31 | Binary Classification | Verified binary target. |
| Adult Income | 1596 | Binary Classification | Verified binary target. |
| Spambase | 1519 | Binary Classification | Verified binary target. |
| WDBC (Diagnosis) | 1511 | Binary Classification | Verified binary target. |
| Vehicle (Bus vs Others) | 1518 | Binary Classification | **Binarized**: 'Bus' vs. {Car, Van, Saab}. |
| SPECT Heart | 1521 | Binary Classification | Verified binary target. |
| Haberman's Survival | 1522 | Binary Classification | Verified binary target. |
| Credit Approval | 1523 | Binary Classification | Verified binary target. |
| Tic-Tac-Toe (Endgame) | 1524 | Binary Classification | Verified binary target. |

*Note: The list above includes multiple distinct datasets. All are verified binary classification tasks available via `sklearn.datasets.fetch_openml`. Each dataset has a unique OpenML ID.*

## Usage

### 1. Download and Cache Datasets
```bash
python code/download_data.py
```
This script will fetch the datasets and store them in `data/raw/` with checksums.

### 2. Run Evaluation
```bash
python code/run_evaluation.py
```
This will execute repeated cross-validation for all datasets and models.
Output: `results/raw_evaluations.csv` (intermediate) -> `results/stability_metrics.csv`.

### 3. Run Analysis
```bash
python code/analyze_stability.py
```
This computes CVs, log-log correlations, and permutation tests.
Output: `results/correlation_results.csv`, `results/permutation_results.csv`.

### 4. Generate Report
```bash
python code/report_generator.py
```
This aggregates the CSVs and fills the `docs/report_template.md`.
Output: `docs/final_report.md`.

## Verification

To verify the installation, run the unit tests:
```bash
pytest tests/unit/
```
To run the full integration test (requires network and a moderate duration):
```bash
pytest tests/integration/test_pipeline.py
```