# Quickstart: The Impact of Perceived Social Support on Resilience to Online Harassment

## Prerequisites
- Python 3.11+
- Git
- Access to the Cyberbullying Survey 2021 dataset (URL required).

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-131-the-impact-of-perceived-social-support-o
 ```

2. **Create and activate virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Configuration
Before running, you must provide the URL for the **Cyberbullying Survey 2021** dataset.
- Edit `code/config/data_config.yaml` and set `dataset_url: "..."`.
- **Critical**: Ensure the URL points to a public, downloadable CSV/Parquet file. If no URL is provided, the pipeline will fail at the ingestion step.

## Running the Pipeline

### 1. Ingest Data
```bash
python code/ingestion.py
```
- Downloads the dataset to `data/raw/`.
- Validates column presence.
- Generates checksum.

### 2. Preprocess & Impute
```bash
python code/preprocessing.py
```
- Applies MICE imputation to predictors.
- Performs listwise deletion on outcomes.
- Saves `data/processed/cleaned_dataset.csv`.

### 3. Run Analysis
```bash
python code/models.py
```
- Fits OLS models with interaction terms.
- Runs BCa Bootstrap with a sufficient number of resamples.
- Applies FDR correction.
- Outputs `data/processed/model_results.json`.

### 4. Generate Report
```bash
python code/report.py
```
- Creates interaction plots and summary tables.
- Saves figures to `data/processed/figures/`.

## Validation
To verify reproducibility:
```bash
pytest tests/
```
- Runs unit tests for scoring logic.
- Runs integration tests for pipeline flow.
- Checks VIF < 5 and other validation criteria.

## Troubleshooting
- **MICE Convergence Failed**: Check for high collinearity or extreme missingness. The pipeline will halt.
- **Dataset Not Found**: Verify `dataset_url` in `config/data_config.yaml`.
- **Memory Error**: Ensure the dataset is < 7 GB. If larger, enable streaming in `ingestion.py`.
- **Data Availability Error**: If the dataset URL is not provided or invalid, the pipeline will fail immediately. Ensure the URL is public and accessible.
