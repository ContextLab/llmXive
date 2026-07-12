# Quickstart: Visual Complexity & Cognitive Load

## Prerequisites

-   Python 3.11+
-   `pip` (Python package manager)
-   `git`
-   Access to the verified stimulus archive (downloaded via `code/stimuli/download.py` or placed manually in `data/stimuli/`).

## Environment Setup

1.  **Clone and Navigate**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-398-the-impact-of-visual-complexity-on-cogni
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins versions for `ultralytics` (CPU), `streamlit`, `statsmodels`, etc.*

## Running the Pipeline

### Step 1: Acquire and Verify Stimuli (P0)
**CRITICAL**: This project uses **real-world meeting background frames** only. No synthetic images are generated.
Download the verified archive and compute checksums.
```bash
python code/stimuli/download.py --source verified_archive_v1
```
*Output*: `data/stimuli/` (real images) and `data/metadata/stimuli.json` (checksums).
*Verification*: The script verifies SHA-256 hashes against the manifest in `data/metadata/stimuli_manifest.json`.

### Step 2: Compute Automated Metrics (P1)
Run the metric extraction pipeline on the verified real images.
```bash
python code/stimuli/compute_metrics.py
```
*Output*: Updates `data/metadata/stimuli.json` with entropy, variance, and object counts.

### Step 3: Run Human Pilot (P0)
Start the Streamlit app to collect human ratings (requires a sufficient number of participants).
```bash
streamlit run code/pilot/app.py
```
*Action*: Open browser, rate images. Data saves to `data/measurements/pilot_ratings.json`.

### Step 4: Validate Metrics (P1)
Check correlation between human ratings and automated metrics.
```bash
python code/pilot/validate.py
```
*Output*: `reports/validation_report.md` (includes scatter plot and r-value).

### Step 5: Run Main Study (P2/P4)
Start the main study app (requires real participants).
```bash
streamlit run code/main_study/app.py
```
*Action*: Participants complete the study. Data saves to `data/measurements/main_study_sessions.json`.

### Step 6: Statistical Analysis (P3)
Run the full analysis pipeline (LMM, VIF, Sensitivity, Null Simulation).
```bash
python code/analysis/lmm.py
python code/analysis/sensitivity.py
python code/analysis/null_simulation.py
```
*Output*: `data/processed/analysis_results.json` and `reports/final_analysis.md`.

## Testing

Run the test suite to verify correctness:
```bash
pytest code/tests/ -v
```

## Reproducibility Check

To ensure reproducibility on a fresh runner:
1.  Delete `data/` and `reports/`.
2.  Run `code/stimuli/download.py` to fetch the verified archive.
3.  Verify checksums in `state/` match.
4.  Run `code/stimuli/compute_metrics.py` and analysis scripts; verify results match `data/processed/analysis_results.json`.