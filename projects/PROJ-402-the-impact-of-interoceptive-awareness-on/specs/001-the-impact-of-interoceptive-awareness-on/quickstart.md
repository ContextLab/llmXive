# Quickstart: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

## Prerequisites

-   Python 3.11+
-   `pip`
-   Git

## Installation

1.  **Clone the repository** and navigate to the project directory.
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

The pipeline is designed to run end-to-end on a CPU-only environment.

### Step 1: Data Audit (Mandatory)
Run the audit script to check for the Schandry task and TSST.
```bash
python code/01_audit_data.py
```
**Output**: `data/audit/data_audit.md` and `data/audit/audit_results.json`.
-   If the script reports "Schandry task NOT found", the pipeline will proceed to generate the Feasibility Report (MDES).
-   If "Schandry task found", proceed to Step 2.

### Step 2: HRV Preprocessing (Conditional)
*Only run if Step 1 confirms the existence of ECG/PPG signals for stress.*
```bash
python code/02_preprocess_hrv.py
```
**Output**: `data/derived/hrv_metrics.csv`.

### Step 3: Analysis (Conditional)
*Only run if Step 1 confirms the existence of the Schandry task.*
```bash
python code/03_analyze_regression.py
```
**Output**: `data/derived/regression_results.csv` and `results/paper_stats.md`.
*If the Schandry task is missing, this script automatically calculates and outputs the Feasibility Report (MDES based on outcome variance + hypothetical R²) instead.*

### Step 4: Versioning Update (Mandatory)
Update the project state with artifact hashes.
```bash
python code/04_update_state.py
```
**Output**: Updated `state/projects/PROJ-402-...yaml` with new artifact hashes (SHA-256).

## Verification

-   **Unit Tests**: Run `pytest tests/` to verify HRV calculation accuracy against the `hrv2` dataset and schema validation.
-   **Reproducibility**: Re-run `main.py` (if created) to ensure checksums match.