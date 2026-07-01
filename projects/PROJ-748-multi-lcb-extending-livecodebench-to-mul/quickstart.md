# Quickstart Guide

## Prerequisites
- Python 3.10+
- Docker (for sandboxed execution)
- Git LFS (for large datasets)

## Installation
```bash
# Clone the repository
git clone <repository-url>
cd PROJ-748-multi-lcb-extending-livecodebench-to-mul

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

## Running the Pipeline

### 1. Download Dataset
```bash
python code/data/download.py
```
This will fetch the Multi-LCB dataset from Hugging Face, verify the checksum, and pin the commit hash.

### 2. Preprocess Data
```bash
python code/data/preprocess.py
```
This converts test cases to a unified format and applies the release-date cutoff.

### 3. Execute Pipeline
```bash
python code/execute_pipeline.py
```
This runs the code generation tasks across multiple languages, temperatures, and models.

### 4. Run Analysis
```bash
python code/analysis/run_analysis.py
```
This computes statistical results including PCA, GLMM, correlations, and significance tests.

### 5. Validate Artifacts
```bash
python code/validation/validate_artifacts.py
```
This ensures all JSON artifacts conform to their schemas.

## Output Files
- `data/multi_lcb_dataset.json`: Downloaded dataset
- `data/preprocessed_dataset.json`: Preprocessed dataset
- `results/artifacts/execution_log.json`: Execution results
- `results/artifacts/statistical_results.json`: Statistical analysis results
- `figures/`: Generated plots and visualizations

## Troubleshooting
- Ensure Docker is running before executing the pipeline
- Check `logs/runtime_failure.log` for execution errors
- Verify checksums match in `data/checksum_info.json`
