# Quickstart: Decoding Affective State from Resting-State EEG Microstates

## Prerequisites

-   Python 3.11+
-   GB RAM available (for dataset loading)
-   Internet access (to fetch verified datasets)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-456-decoding-affective-state-from-resting-st/code
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
    *Note: `requirements.txt` pins CPU-compatible versions of `mne`, `scikit-learn`, and `numpy`.*

## Running the Pipeline

### Step 1: Download and Verify Data
The pipeline will automatically attempt to download data from the verified URLs defined in `research.md`.
```bash
python main.py --stage download
```
*Output*: Raw data saved to `data/raw/` with checksums. **Warning**: If linked affective data is not found, the pipeline will log "No Linked Data" and skip the analysis phase.

### Step 2: Preprocess EEG
Apply bandpass filter, ICA, and re-referencing.
```bash
python main.py --stage preprocess
```
*Output*: Cleaned EEG in `data/processed/cleaned_eeg/`.

### Step 3: Microstate Segmentation
Segment EEG into 4 classes using a **pre-defined literature template** and extract features.
```bash
python main.py --stage segment
```
*Output*: Feature matrices in `data/processed/features.csv`.

### Step 4: Correlation Analysis
Compute correlations, apply **Holm-Bonferroni** correction, and run bootstrap (with N<20 flag if applicable).
```bash
python main.py --stage analyze
```
*Output*: Results in `data/outputs/correlation_results.csv` and `data/outputs/bootstrap_stability.json`.

### Step 5: Sensitivity Analysis
Sweep thresholds and report stability.
```bash
python main.py --stage sensitivity
```
*Output*: Sensitivity report in `data/outputs/sensitivity_analysis.json`.

### Step 6: Validation
Run unit tests and schema validation.
```bash
pytest tests/
python main.py --stage validate
```

## Troubleshooting

-   **Memory Error**: If RAM usage exceeds 7GB, the pipeline will automatically sample subjects. Ensure `data/` is on a fast disk (SSD).
-   **No Linked Data**: If no subjects are found in both EEG and Affective datasets, the pipeline logs "No Linked Data" and skips the analysis phase. This is expected given the current verified sources.
-   **Bootstrap Warning**: If N < 20, results will be flagged as "Unstable". Analytical p-values are still provided.
-   **Collinearity**: Holm-Bonferroni correction is applied by default to handle dependency among tests.
