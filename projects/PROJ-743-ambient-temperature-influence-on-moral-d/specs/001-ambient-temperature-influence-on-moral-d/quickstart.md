# Quickstart: Ambient Temperature Influence on Moral Decision Speed

## Prerequisites

- Python 3.11 or higher.
- Access to the project repository (`projects/PROJ-743-ambient-temperature-influence-on-moral-d`).
- Internet access to download datasets (if not pre-cached).
- **Critical**: A verified source for ERA5 data covering 2016-2019 must be available in the project's verified datasets block.

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-743-ambient-temperature-influence-on-moral-d
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins specific versions to ensure reproducibility.*

## Data Setup

The project requires two datasets:
1. **Moral Machine**: Download the CSV from the canonical source (refer to `research.md` for source details).
2. **ERA5**: Download the verified HDF5 file (`era5_2016_2019.h5`) covering the 2016-2019 period from the HuggingFace link provided in the verified datasets block.

**WARNING**: The provided ERA5 file `1982_1.h5` is **NOT** suitable. You must use a verified source for 2016-2019.

Place the raw files in `data/raw/`:
```text
data/raw/
├── moral_machine.csv
└── era5_2016_2019.h5  # (Required: verified source for 2016-2019)
```

## Running the Pipeline

The pipeline is executed in three stages:

### 1. Data Ingestion & Merging
```bash
python code/ingest.py
```
- **Output**: `data/processed/merged_analysis.parquet`, `results/logs/exclusion_log.csv`.
- **Logs**: Check `results/logs/exclusion_log.csv` for records excluded due to distance, time gaps, or data mismatch.
- **Validation**: The script will halt if the ERA5 data does not cover 2016-2019.

### 2. Model Fitting
```bash
python code/model.py
```
- **Output**: `results/stats/model_summary.json`, `results/figures/diagnostics.png`.
- **Note**: This step may take 30-60 minutes on a CPU runner depending on sample size. Subsampling (100k records) is applied if necessary.

### 3. Robustness Analysis
```bash
python code/robustness.py
```
- **Output**: `results/stats/robustness_table.csv`, `results/figures/sensitivity_plots.png`.

## Verifying Results

- **Model Convergence**: Check `results/stats/model_summary.json` for `convergence_status: true`.
- **Diagnostic Plots**: Open `results/figures/diagnostics.png` to verify normality of residuals (including Anderson-Darling test results).
- **Sensitivity**: Review `results/stats/robustness_table.csv` to ensure the temperature coefficient is stable across thresholds.

## Troubleshooting

- **Memory Error**: If the model fails due to memory, reduce the sample size in `code/ingest.py` (e.g., `sample_size=50000`).
- **ERA5 Mismatch**: If no records are matched, verify the timestamp range of the ERA5 file matches the Moral Machine data (2016-2019).
- **Convergence Warnings**: If the model does not converge, try simplifying the random effects structure (e.g., remove `cultural_region` random intercept) or use fixed-effects only.
- **Data Validation Error**: If the script halts with "Fatal Data Gap", ensure a verified ERA5 source for 2016-2019 is added to the verified datasets block.