# Quickstart: Predicting Cognitive Fatigue from Resting-State EEG Complexity

## Prerequisites

-   Python 3.11+
-   Git
-   Access to Hugging Face (for dataset download)
-   14 GB free disk space

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-470-predicting-cognitive-fatigue-from-restin
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

## Configuration

Edit `code/config.yaml` to set parameters (optional, defaults provided):
```yaml
eeg:
  filter_low: 1.0
  filter_high: 40.0
  notch_freq: 50.0
  artifact_threshold_uv: 100.0
  min_segment_sec: 120
analysis:
  correlation_method: "spearman"
  fdr_method: "bh"
  vif_threshold: 5.0
```

## Running the Pipeline

### 1. Download and Validate Data
This step downloads data from the verified Hugging Face sources and checks for paired EEG/Fatigue data.
```bash
python code/download.py --validate
```
*Output*: `data/manifests/data_manifest.json` and error logs if data is missing.

### 2. Preprocess EEG
Applies filters and artifact rejection.
```bash
python code/preprocess.py
```
*Output*: `data/processed/cleaned_eeg/` containing `.fif` files.

### 3. Extract Complexity Features
Calculates LZC and Permutation Entropy.
```bash
python code/features.py
```
*Output*: `data/analysis/complexity_metrics.csv`.

### 4. Run Correlation Analysis
Performs statistical tests, VIF checks, and BH correction.
```bash
python code/analysis.py
```
*Output*: `data/analysis/correlation_results.csv` and `data/analysis/report_summary.txt`.

### 5. Generate Final Report
```bash
python code/report.py
```
*Output*: `data/analysis/final_report.pdf`.

## Testing

Run the test suite to verify the pipeline:
```bash
pytest tests/ -v
```
*Key Tests*:
-   `test_preprocess_notch_filter`: Verifies 50 Hz attenuation.
-   `test_complexity_synthetic`: Verifies LZC/PE on synthetic signals.
-   `test_correlation_mock`: Verifies p-values on mock data.
