# Quickstart: Assessing the Stability of Statistical Model Performance Across Data Subsets

## Prerequisites

-   Python 3.10 or higher.
-   `pip` package manager.
-   Internet connection (for initial dataset download).

## Installation

1.  **Clone the repository** (or navigate to the project root).
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

The pipeline is executed sequentially. Run the following commands in order:

### Step 1: Download Datasets (One-Time Setup)
Fetches a set of pre-verified binary classification datasets from OpenML and caches them.
**Important**: This step must be run **once** before the main evaluation. The CI execution assumes these files are present.
```bash
python code/download_data.py
```
*Output*: `data/raw/` directory with 15 CSV files and `data/checksums.txt`.

### Step 2: Execute Evaluations
Runs the repeated cross-validation for all datasets and models.
```bash
python code/run_evaluation.py
```
*Output*: `results/stability_metrics.csv`.
*Note*: This step may take several hours.

### Step 3: Analyze Stability
Calculates log-log correlations and runs block permutation tests.
```bash
python code/analyze_stability.py
```
*Output*: `results/correlation_results.csv`, `results/permutation_results.csv`.

### Step 4: Generate Report
Aggregates results and generates the final Markdown report.
```bash
python code/report_generator.py
```
*Output*: `results/final_report.md`.

## Dataset List

The pipeline uses a set of binary classification datasets (pre-verified OpenML IDs):
1.  **1590** (Adult) - Income prediction
2.  **1464** (Bank Marketing) - Subscription
3.  **1479** (Credit Approval) - US/UK (N=690)
4.  **1468** (German Credit)
5.  **1476** (Pima Indians Diabetes) - N=768, F=8
6.  **1461** (Heart Disease) - Cleveland (N=303)
7.  **1510** (Breast Cancer Wisconsin) (N=699)
8.  **1482** (Ionosphere) (N=351)
9.  **1471** (Spambase)
10. **1463** (Vehicle) - Binary subset (van vs other)
11. **1472** (Soybean) - Binary subset (diaporthe vs other)
12. **1486** (Hypothyroid)
13. **1488** (Letter Recognition) - Binary subset (a vs b)
14. **1490** (Magic Gamma Telescope)
15. **1492** (MiniBooNE)

*Note*: All datasets are pre-verified to be binary classification tasks with sample sizes ranging from small to large scales.

## Verification

To verify the installation and a single run (without the full 15 datasets):
1.  Edit `code/config.py` to set `TEST_MODE = True`.
2.  Run `python code/run_evaluation.py`.
3.  Check `results/stability_metrics.csv` for non-zero variance.
