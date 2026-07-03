# Quickstart: Predicting Cognitive Fatigue from Resting-State EEG Complexity

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution) or a local Linux environment.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/your-repo.git
    cd your-repo
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

    *Note: `requirements.txt` pins all versions to ensure reproducibility.*

## Running the Pipeline

The pipeline is executed via a single entry point script.

### 1. Download Data
```bash
python code/download.py
```
This script will:
- Fetch data from the verified URLs.
- Validate the presence of required variables (EEG + Fatigue).
- **Crucially**: Check if the dataset supports a longitudinal (pre/post) design. If not, it will log a warning and prepare for cross-sectional analysis.
- Save raw data to `data/raw/` and generate checksums.

### 2. Preprocess Data
```bash
python code/preprocess.py
```
This script will:
- Apply bandpass filter (1-40 Hz).
- Remove line noise (50 Hz).
- Reject artifacts (> ±100 µV).
- Save preprocessed segments to `data/processed/segments/`.

### 3. Extract Features
```bash
python code/features.py
```
This script will:
- Calculate Lempel-Ziv Complexity and Permutation Entropy.
- Save features to `data/processed/features/complexity_metrics.csv`.

### 4. Run Analysis
```bash
python code/analysis.py
```
This script will:
- Detect data structure (longitudinal vs. cross-sectional).
- Perform ANCOVA (if longitudinal) or Correlation (if cross-sectional).
- Apply Benjamini-Hochberg correction.
- Run sensitivity analysis.
- Save results to `data/processed/results/correlation_results.csv`.

### 5. Generate Report
```bash
python code/report.py
```
This script will:
- Generate a PDF report with figures and tables.
- Save to `docs/report.pdf`.

## Verification

To verify the pipeline on a sample dataset:

1.  Run `python tests/integration/test_pipeline.py`.
2.  Check that the output includes:
    - Attenuation of 50 Hz line noise (>20 dB).
    - Valid complexity values for synthetic signals.
    - Correct p-value correction.
    - Confirmation of the analysis model used (ANCOVA vs. Correlation).

## Troubleshooting

- **Memory Error**: If you encounter "MemoryError", ensure you are not loading the entire dataset at once. The pipeline is designed to process data in chunks.
- **Dataset Missing Variables**: If the script halts with "Dataset lacks required variables", check the `research.md` for the list of verified datasets and their schemas.
- **Import Errors**: Ensure you are using Python 3.11 and the correct virtual environment.