# Quickstart: Identifying Predictive Biomarkers of Chemotherapy Response

## Prerequisites

- Python 3.11+
- Git
- Docker (for R environment)
- Access to GitHub Actions (for CI) or local environment with Docker

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-135-identifying-predictive-biomarkers-of-che
    ```

2.  **Build the Docker container**:
    ```bash
    docker build -t biomarker-r-env -f src/Dockerfile .
    ```

3.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

### 1. Data Acquisition
Download metadata and real expression data from GDC and GEO.
```bash
python src/data_acquisition.py --mode real --subset-size
```
*Note: `--subset-size` is used to limit data volume for the GB RAM constraint. Use `--mode full` if you have more resources.*

### 2. Preprocessing
Harmonize gene IDs and normalize data (VST/RMA).
```bash
python src/preprocessing.py
```

### 3. Differential Expression
Run DE analysis for each tumor type using DESeq2.
```bash
python src/differential_expression.py
```

### 4. Meta Analysis
Combine results and select gene panel.
```bash
python src/meta_analysis.py
```

### 5. Model Training & Validation
Train models and perform LOO/external validation.
```bash
python src/loo_controller.py
```

### 6. View Results
Check `results/summary.md` for the final report.

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

## Troubleshooting

- **Docker Error**: Ensure Docker is installed and running. Rebuild the container if necessary.
- **Missing Data**: If the pipeline reports "No response labels found", it has skipped that dataset. Check `data/raw/` for the downloaded files.
- **RAM Error**: If you encounter OOM, reduce the `--subset-size` parameter in `data_acquisition.py`.
- **R Dependencies**: The R environment is provided by the Docker container. Do not attempt to install R packages globally.
