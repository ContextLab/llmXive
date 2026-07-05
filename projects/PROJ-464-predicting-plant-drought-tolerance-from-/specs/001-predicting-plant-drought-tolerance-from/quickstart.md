# Quickstart: Predicting Plant Drought Tolerance from RSA Data

## Prerequisites

- Python 3.11+
- Git
- Access to the project repository

## Installation

1.  **Clone and Setup Environment**
    ```bash
    git clone <repository-url>
    cd projects/PROJ-464-predicting-plant-drought-tolerance-from-/
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**
    ```bash
    python -c "import cv2, sklearn, statsmodels; print('Dependencies OK')"
    ```

## Running the Pipeline

The pipeline is executed via the `main.py` entry point.

### Step 1: Data Download (MGB3 & TRY)
The script fetches MGB3 images and TRY data.
```bash
python code/download.py
```
*Output*: `data/raw/mgb3_images/`, `data/raw/try_data.csv`

### Step 2: Preprocessing & Merging
This step processes images (OpenCV) to generate RSA metrics and merges with physiological data.
```bash
python code/preprocess.py
```
*Output*: `data/derived/study_data.csv`

### Step 3: Model Training & Analysis
This step runs Ridge/Lasso and LMM, followed by sensitivity analysis.
**Note**: Classification (FR-007/FR-008) is skipped due to circular validation.
```bash
python code/main.py
```
*Output*: `data/derived/model_results.json`, `figures/correlation_matrix.png`, `figures/sensitivity_plot.png`

## Validation

Run the test suite to ensure the pipeline is reproducible:
```bash
pytest tests/ -v
```

## Troubleshooting

- **Memory Error**: If the dataset is too large, reduce the sample size in `code/config.py` (e.g., `MAX_SAMPLES = 1000`).
- **Missing Species**: If species names do not match between datasets, check the `species_name` column for formatting differences.
- **Underpowered Study**: If N < 30, the pipeline will halt and report "Underpowered".
