# Quickstart: Quantifying Hallucination in LLM-Generated API Documentation

## Prerequisites

- Python 3.11+
- Git
- Access to Hugging Face Hub (no token required for public datasets)
- 7 GB RAM (GitHub Actions free tier)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-762-quantifying-hallucination-in-llm-generat/code
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `transformers`, `torch` (CPU), `spacy`, `radon`, `pandas`, `scikit-learn`, `datasets`.*

4.  **Download spaCy model**:
    ```bash
    python -m spacy download en_core_web_sm
    ```

## Running the Pipeline

### Step 1: Download Data (Streaming)
Download a sample of the CodeSearchNet dataset (streaming to save RAM):
```bash
python src/download.py --sample-size 1000 --streaming
```
*Output: `data/processed/features.csv` (partial)*

### Step 2: Generate Descriptions
Run the generation pipeline for both models:
```bash
python src/generate.py --models codegen-350M starcoderbase-1b --batch-size 1
```
*Output: `data/processed/generations.csv`*

### Step 3: Compute Metrics
Calculate entity-overlap F1 scores:
```bash
python src/metrics.py
```
*Output: `data/processed/metrics.csv`*

### Step 4: Run Analysis
Perform correlation, regression, and sensitivity analysis:
```bash
python src/analysis.py
```
*Output: `data/results/analysis_report.json`*

### Step 5: Validation (Optional)
Run the manual validation logic (requires manual annotation of a subset):
```bash
python src/validate.py --subset-size 0.05
```
*Output: `data/results/validation_report.json`*

## Expected Outputs

- `data/processed/metrics.csv`: Contains the hallucination index for every function.
- `data/results/analysis_report.json`: Contains correlation coefficients, p-values, and sensitivity data.
- `data/results/validation_report.json`: Contains the correlation between automated and manual scores.

## Troubleshooting

- **OOM Error**: If you encounter `MemoryError`, reduce the `--batch-size` to 1 and ensure `--streaming` is enabled during download.
- **Model Loading**: If `codegen-350M` fails to load, ensure `torch` is installed in CPU mode (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
- **AST Parsing Errors**: Functions with syntax errors will be skipped and logged. Check `logs/preprocess.log` for details.
