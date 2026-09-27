# Predicting Plant Drought Tolerance from Root System Architecture (RSA) Data

This project implements a scientific pipeline to predict plant drought tolerance using quantitative Root System Architecture (RSA) metrics derived from root images and physiological trait data.

## Overview

The pipeline processes root images from the NPPN Plant Phenome Pipeline to extract RSA metrics (depth, branching density, surface area), merges them with physiological traits from the TRY database, and applies statistical models (OLS, Ridge, Lasso, Random Forest, PGLS) to identify predictors of drought tolerance.

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Access to HuggingFace Hub (for NPPN images)
- TRY API Key (for physiological traits)

### Setup

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-464-predicting-plant-drought-tolerance-from
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. Configure environment variables:
 ```bash
 export TRY_API_KEY="your_try_api_key_here"
 ```

## Usage

The pipeline is executed in sequential stages. Run each script in order to process data and generate results.

### 1. Download Root Images

Fetches root images from the NPPN Plant Phenome Pipeline on HuggingFace.

```bash
python code/download_images.py
```

**Output**: `data/raw/nppn_images/`

### 2. Preprocess Images & Extract RSA Metrics

Processes images to extract depth, branching density, and surface area.

```bash
python code/preprocess_images.py
```

**Output**: `data/derived/rsametrics.csv`

### 3. Download Physiological Traits

Fetches stomatal conductance and photosynthesis data from the TRY database.

```bash
python code/download_traits.py
```

### 4. Merge Data

Combines RSA metrics with physiological traits.

```bash
python code/merge_data.py
```

**Output**: `data/derived/merged_data.csv`

### 5. Fetch Phylogenetic Tree

Retrieves the phylogenetic tree from Open Tree of Life.

```bash
python code/fetch_phylogeny.py
```

**Output**: `data/derived/phylogenetic_tree.newick`

### 6. Run Statistical Models

Fits OLS, Ridge, Lasso, Random Forest, and PGLS models.

```bash
python code/models.py
```

**Output**: `data/derived/model_results.csv`, `data/derived/pgls_results.csv`

### 7. Run Sensitivity Analysis

Performs threshold sensitivity analysis for classification models.

```bash
python code/analysis.py
```

**Output**: `data/derived/sensitivity_sweep_results.csv`, `results/figures/sensitivity_curve.png`

### 8. Generate Final Report

Creates the final analysis report with VIF compliance checks.

```bash
python code/generate_report.py
```

**Output**: `data/derived/report_framing.md`, `state/vif_compliance_check.yaml`

## Project Structure

```
.
├── code/ # Implementation modules
│ ├── config.py # Configuration and paths
│ ├── models.py # Data models and ML models
│ ├── analysis.py # Statistical analysis functions
│ ├── download_images.py # Image download logic
│ ├── preprocess_images.py # Image processing
│ ├── download_traits.py # Trait data download
│ ├── merge_data.py # Data merging logic
│ ├── fetch_phylogeny.py # Phylogenetic tree fetching
│ ├── generate_report.py # Report generation
│ └──...
├── data/
│ ├── raw/ # Raw downloaded images
│ └── derived/ # Processed data and results
├── contracts/ # Data validation schemas
├── state/ # Intermediate state files
├── results/ # Final outputs and figures
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Results

The pipeline generates the following key artifacts:

- **RSA Metrics**: `data/derived/rsametrics.csv` - Quantitative root architecture traits
- **Merged Dataset**: `data/derived/merged_data.csv` - Combined RSA and physiological data
- **Model Results**: `data/derived/model_results.csv` - Statistical model coefficients and metrics
- **PGLS Results**: `data/derived/pgls_results.csv` - Phylogenetic generalized least squares results
- **Sensitivity Analysis**: `data/derived/sensitivity_sweep_results.csv` - Threshold robustness data
- **Final Report**: `data/derived/report_framing.md` - Comprehensive analysis summary
- **VIF Compliance**: `state/vif_compliance_check.yaml` - Collinearity verification status

## Testing

Run the test suite to verify pipeline integrity:

```bash
pytest tests/
```

Specific test modules:
- `tests/unit/test_image_processing.py` - Image processing logic
- `tests/integration/test_image_pipeline.py` - End-to-end image pipeline
- `tests/unit/test_model_fitting.py` - Model fitting logic
- `tests/integration/test_model_pipeline.py` - End-to-end model pipeline
- `tests/unit/test_sensitivity.py` - Sensitivity analysis logic
- `tests/integration/test_sensitivity.py` - End-to-end sensitivity analysis

## Dependencies

See `requirements.txt` for the full list of dependencies including:
- pandas, numpy, scikit-learn, scipy
- statsmodels, opencv-python-headless, scikit-image
- requests, huggingface_hub, caper, pytest, networkx

## License

This project is part of the llmXive automated science pipeline.