# Quickstart: Investigating the Correlation Between Gut Microbiome Composition and Circadian Rhythm Disruption

## Prerequisites

- **Python**: 3.11 or higher.
- **Git**: For cloning the repository.
- **Access to Datasets**:
  - **American Gut Project (AGP)**: You must have access to the AGP data. This typically requires registering on the Open Humans platform and joining the American Gut Project study. Download the 16S rRNA data and associated metadata.
  - **Open Humans Sleep Survey**: Ensure you have access to the sleep survey data. **Specific Project ID Required**: The plan requires the "Sleep and Circadian Rhythm" project (Project ID: `12345` - *placeholder to be replaced with actual verified ID*). Verify that this project contains the variables `sleep_duration`, `sleep_quality`, and `chronotype`.

> **Note**: The "Verified datasets" block in the project specification does not provide direct download URLs for the full AGP or Open Humans sleep datasets. You may need to download these manually from the official platforms and place them in `data/raw/`. **If the specific Open Humans project lacks the required variables, the study cannot proceed.**

## Critical Data Bridging Requirement

**Important**: The American Gut Project and Open Humans datasets often use different ID schemes (e.g., hashed IDs vs. UUIDs). A direct merge is **not guaranteed** to work.
- **Bridging Key**: If a public bridging dataset exists that maps AGP IDs to Open Humans IDs, download it and place it in `data/raw/bridging/`.
- **Manual Reconciliation**: If no bridging key is available, you must manually reconcile the IDs or the pipeline will halt with N=0.
- **Verification**: Before running the pipeline, verify that the `participant_id` formats match between AGP and Open Humans. If they do not, the merge will fail.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-037-investigating-the-correlation-between-gu
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Setup

1. **Download AGP Data**:
   - Obtain the 16S rRNA OTU/ASV table and metadata from the American Gut Project.
   - Place the files in `data/raw/agp/`.

2. **Download Open Humans Sleep Data**:
   - Obtain the sleep survey metadata from the specific Open Humans project (e.g., Project ID: 12345).
   - Place the files in `data/raw/open_humans/`.

3. **Verify Data**:
   - Ensure the files are in CSV/TSV format and contain the expected columns (Participant ID, Age, BMI, Sleep Duration, Chronotype).
   - **Critical**: Verify that `participant_id` formats match between AGP and Open Humans. If they do not, the merge will fail.

## Running the Pipeline

The pipeline is executed via a single script that orchestrates ingestion, analysis, and validation.

1. **Run the full pipeline**:
   ```bash
   python code/main.py
   ```
   This will:
   - Download (if configured) and merge data.
   - Calculate diversity metrics.
   - Perform correlation and GLM analysis.
   - Run bootstrap resampling and sensitivity analysis.
   - Generate the final report.

2. **Run specific modules**:
   - **Ingestion**: `python code/ingestion.py`
   - **Analysis**: `python code/analysis.py`
   - **Validation**: `python code/validation.py`
   - **Visualization**: `python code/viz.py`

## Expected Outputs

- `data/processed/merged_cohort.csv`: The cleaned, analysis-ready dataset.
- `data/outputs/correlation_results.csv`: Table of correlation coefficients and p-values.
- `data/outputs/bootstrap_results.json`: Confidence intervals from resampling.
- `data/outputs/figures/`: Heatmaps, PCoA plots, and sensitivity charts.
- `reports/final_report.md`: The human-readable report with associational findings.

## Troubleshooting

- **Missing Data**: If the merged cohort size (N) is less than 200, the pipeline will flag a power limitation. Check the `data/raw/` directories to ensure all expected files are present.
- **ID Mismatch**: If the merge fails, verify that the `participant_id` columns in both datasets are formatted identically (e.g., no leading/trailing whitespace). **If IDs are fundamentally incompatible (e.g., hashed vs UUID), the study halts.** Check if a bridging key is required and available.
- **Memory Errors**: If you encounter memory issues, ensure you are using `scipy.sparse` matrices and that the OTU table is not loaded into memory unnecessarily.

## Reproducibility

To ensure reproducibility, all random seeds are pinned in the code. To re-run the analysis on a fresh environment:
```bash
rm -rf data/processed data/outputs
python code/main.py
```
Verify that the output files match the checksums recorded in the project state file.