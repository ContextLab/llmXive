# Reconstructing Solar Irradiance from Historical Sunspot Records

This project implements a pipeline to reconstruct Total Solar Irradiance (TSI) using historical sunspot numbers (GSN) and satellite-era TSI measurements. It employs machine learning models (Random Forest, Gaussian Process) with cycle-specific features and a fallback mechanism for pre-satellite eras.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Virtual environment tool (venv, conda, or similar)

## Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd PROJ-381-reconstructing-solar-irradiance-from-his
 ```

2. **Create and activate a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 Ensure you are in the project root directory and run:
 ```bash
 pip install -r requirements.txt
 ```

 *Note: `requirements.txt` includes pinned versions for `pandas`, `scikit-learn`, `numpy`, `scipy`, `requests`, `pyyaml`, and `joblib`.*

4. **Configure Environment Variables**:
 The project relies on environment variables for data paths and API endpoints.
 - Copy the example environment file if available:
 ```bash
 cp.env.example.env
 ```
 - Edit `.env` to set the following variables (or set them directly in your shell):
 - `DATA_PATH`: Path to the `data/` directory.
 - `SILSO_URL`: URL for the SILSO sunspot number data.
 - `SORCE_URL`: URL for the SORCE/TIM TSI data.
 - Alternatively, run the environment setup script provided in `code/env_manager.py` logic by ensuring these variables are exported in your shell session before running the pipeline.

5. **Verify Installation**:
 Run the setup verification script to ensure all directories and dependencies are correctly configured:
 ```bash
 python code/setup_structure.py
 ```

## Usage

The pipeline is executed in stages. Ensure the virtual environment is activated.

1. **Data Ingestion**:
 Fetch raw GSN and TSI data from SILSO and SORCE.
 ```bash
 python code/data/ingestion.py
 ```
 *Output: `data/raw/silso_gsn.csv`, `data/raw/sorce_tsi.csv`*

2. **Preprocessing**:
 Merge datasets, fill gaps (using GSN=0 proxy for long gaps), and detect cycle boundaries.
 ```bash
 python code/data/preprocessing.py
 ```
 *Output: `data/processed/preprocessed_data.parquet`*

3. **Model Training**:
 Train Random Forest and Gaussian Process models using Leave-One-Cycle-Out (LOCO) cross-validation.
 ```bash
 python code/models/train.py
 ```
 *Outputs: `code/models/artifacts/best_model.joblib`, `data/processed/cv_report.json`*

4. **Fallback Model Training**:
 Train the Cycle-Agnostic fallback model and derive cycle-specific offsets.
 ```bash
 python code/models/train_fallback.py
 ```
 *Outputs: `code/models/artifacts/fallback_model.joblib`, `data/processed/cycle_specific_coefficients.json`*

5. **Sensitivity Analysis**:
 Evaluate model stability against inconsistency tolerance thresholds.
 ```bash
 python code/analysis/sensitivity.py
 ```
 *Output: `data/processed/sensitivity_report.json`*

6. **Reconstruction Generation**:
 Apply models to the pre-satellite GSN record (1610–2002).
 ```bash
 python code/analysis/generate_reconstruction.py
 ```
 *Output: `data/processed/reconstruction_1610_2002.parquet`*

7. **Variance Analysis**:
 Perform bootstrap resampling to compare variance across historical minima.
 ```bash
 python code/analysis/generate_variance_analysis.py
 ```
 *Output: `data/processed/variance_analysis.json`*

8. **Baseline Comparison**:
 Compare the new reconstruction against the 2007 baseline and CMIP6 data.
 ```bash
 python code/analysis/comparison.py
 ```
 *Output: `data/processed/final_report.md`*

## Testing

Run the test suite to verify functionality:
```bash
pytest tests/
```

## Project Structure

```text
.
├── code/
│ ├── analysis/
│ ├── data/
│ ├── models/
│ ├── config.py
│ ├── env_manager.py
│ └──...
├── data/
│ ├── raw/
│ └── processed/
├── tests/
├── contracts/
├── docs/
├── requirements.txt
└── README.md
```

## License

[Insert License Information Here]