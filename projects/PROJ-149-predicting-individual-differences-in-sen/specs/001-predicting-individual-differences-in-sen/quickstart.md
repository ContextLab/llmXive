# Quickstart: Predicting Individual Differences in Sensory Processing Speed from Resting‑State EEG Power Spectra

## Prerequisites

- Python 3.11+
- Sufficient available RAM (GitHub Actions free tier)
- Internet access to download datasets from HuggingFace

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
    *Note: `requirements.txt` pins versions to ensure reproducibility on CPU-only runners.*

## Running the Pipeline

The pipeline is executed in stages via the scripts in `code/`.

### Step 1: Download Data
```bash
python code/01_download_data.py
```
*Downloads raw EEG and RT data to `data/raw/` and verifies checksums.*

### Step 2: Data Feasibility Gate
```bash
python code/01_download_data.py --check-feasibility
```
*Attempts to join datasets and verify task compatibility. If failed, generates `data/processed/feasibility_report.md` and halts.*

### Step 3: Preprocess & Extract Features
```bash
python code/02_preprocess_eeg.py
python code/03_extract_features.py
```
*Applies filters, ICA, computes PSD (2s windows, [deferred] overlap), applies CLR transformation, and generates `data/processed/features.csv`.*

### Step 4: Modeling & Analysis
```bash
python code/04_modeling.py
```
*Fits Linear/LASSO models, runs permutation tests (on test set only), calculates MDES, and saves results.*

### Step 5: Robustness & Sensitivity
```bash
python code/05_robustness_analysis.py
python code/06_sensitivity_analysis.py
```
*Generates robustness reports and sensitivity plots.*

### Step 6: Final Report
```bash
python code/generate_report.py
```
*Aggregates all findings into `data/processed/final_report.md`.*

## Verification

To verify the pipeline on a subset:
1.  Set `config.py` variable `SAMPLE_SIZE = 10`.
2.  Run `python code/01_download_data.py`.
3.  Run the full pipeline.
4.  Check `data/processed/features.csv` for 10 rows.
5.  Check `data/processed/model_results.json` for valid R², Adjusted R², and p-values.

## Troubleshooting

- **Memory Error**: The pipeline processes data in chunks. If you still hit memory limits, reduce `SAMPLE_SIZE` in `config.py`.
- **Dataset Mismatch**: If the script reports "No matched participants", the EEG and RT datasets do not share IDs or the tasks are incompatible. This is a data availability issue, not a code error.
- **Permutation Test Timeout**: If the permutation test with a large number of permutations takes too long, reduce `N_PERMUTATIONS` in `config.py` (e.g., to 1000) for debugging.