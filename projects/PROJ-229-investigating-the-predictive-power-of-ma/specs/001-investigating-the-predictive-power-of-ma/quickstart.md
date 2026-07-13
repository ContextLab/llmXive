# Quickstart: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

## Prerequisites

- Python 3.11+
- Materials Project API Key (set as `MP_API_KEY` environment variable)
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-229-investigating-the-predictive-power-of-ma
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

4.  **Set environment variables**:
    ```bash
    export MP_API_KEY="your-api-key-here"
    ```

## Running the Pipeline

### 1. Data Retrieval and Feature Engineering
```bash
python code/data/fetch_materials_project.py
python code/data/compute_descriptors.py
```
*Output: `data/features.csv`*

### 2. Model Training
```bash
python code/models/train_baselines.py
python code/models/train_symbolic.py
```
*Output: `data/model_results.json`, `data/shap_analysis.json`*

### 3. Validation and Analysis
```bash
python code/models/evaluate.py
```
*Output: `data/validation_results.csv`, `reports/sensitivity_analysis.pdf`*

## Verification

To verify the pipeline:
```bash
pytest tests/
```

## Troubleshooting

- **API Rate Limits**: If the script fails due to rate limits, wait and retry. The script includes exponential backoff.
- **Memory Errors**: If memory usage exceeds 7 GB, reduce the sample size in `code/config.yaml`.
- **PySR Timeout**: If PySR does not converge, check `data/model_results.json` for fallback SHAP results.
