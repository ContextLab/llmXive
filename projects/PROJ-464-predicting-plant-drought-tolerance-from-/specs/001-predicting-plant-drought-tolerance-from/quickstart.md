# Quickstart: Predicting Plant Drought Tolerance from RSA Data

## Prerequisites

- Python 3.10+
- Git
- Access to a Linux environment (GitHub Actions runner or local Linux VM).
- **Real NPPN Root Images**: Place root images in `data/raw/nppn_images/`. The pipeline will fail if this directory is empty.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-464-predicting-plant-drought-tolerance-from-/code
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Preparation

### Option A: Using Verified Datasets (Recommended)
The pipeline will automatically download the TRY traits and the RSA benchmark dataset (for unit tests only) if raw images are missing.

1. **Run the download script**:
   ```bash
   python scripts/download_data.py
   ```
   *Note: This script checks for raw images. If none are found, it downloads the `RSA (Parquet)` and `TRY` datasets to `data/raw/` for format validation, but the main pipeline will halt if no real images are present.*

### Option B: Using Local Images
1. Place root images in `data/raw/nppn_images/`.
2. Ensure filenames follow the pattern: `{species_name}_{id}.png`.
3. Run the download script (it will skip downloading if images exist).

## Running the Pipeline

Execute the full pipeline in sequence:

```bash
# 0. Fetch Phylogeny (Mandatory, with PVR fallback)
python scripts/fetch_phylogeny.py

# 1. Extract RSA metrics
python scripts/extract_rsa.py

# 2. Merge data
python scripts/merge_data.py

# 3. Analyze collinearity & run PCA
python scripts/analyze_collinearity.py

# 4. Fit models & run sensitivity analysis (if proxy exists)
python scripts/fit_models.py

# 5. Generate report
python scripts/generate_report.py
```

## Verification

To verify the pipeline on a small scale (format validation only):

```bash
pytest tests/ -v
```

This runs unit tests on image extraction (using a mock image) and data merging logic. **Note:** These tests do not validate biological predictions.

## Output

- **Results**: `results/reports/summary_report.md`
- **Figures**: `results/figures/`
- **Data**: `data/derived/merged_data.csv`, `data/derived/model_results.json`