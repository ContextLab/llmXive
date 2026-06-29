# Quickstart: Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

## Prerequisites

- Python 3.x or higher
- Docker (optional, for containerized execution)
- Git
- Sufficient free disk space (≈ 2 GB)

## Installation

### Option 1: Local Execution (Recommended for Development)

```bash
# Clone repository
git clone <repo-url>
cd projects/PROJ-147-uncovering-correlations-between-processi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Containerized Execution (Recommended for CI)

```bash
# Build Docker image
docker build -t texture-pipeline:latest .

# Run pipeline
docker run -v $(pwd)/data:/app/data texture-pipeline:latest python code/main.py
```

## Running the Pipeline

### Full End-to-End Execution

```bash
python code/main.py --mode full
```

This will:
1. **Download** datasets from verified sources (OMDB, NIST) **or** generate **synthetic** data when paired data are missing (see `research.md` for details).  
2. **Preprocess** and validate data (standardization, median imputation, outlier removal).  
3. **Train** a multi‑output RandomForest model (5‑fold CV, grid search).  
4. **Evaluate** and generate reports (R², MAE, RMSE, importance plot).  
5. **Output** predictions and importance visualisation **(pipeline validated on synthetic data only)**; real‑world predictions will be possible once genuine paired data are supplied.

### Predicting New Samples

```bash
python code/main.py --mode predict --input new_samples.csv --output new_predictions.csv
```

### CI Execution (GitHub Actions)

```yaml
# .github/workflows/ci.yaml
name: Texture Pipeline CI
on: [push, pull_request]
jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run pipeline
        run: python code/main.py --mode full
```

## Limitations

- **Synthetic Data Only**: The current pipeline operates **only** on synthetic data because **no** verified public dataset provides paired rolling‑process parameters **and** texture measurements. This limitation limits the scientific conclusions we can draw about real material behavior; the pipeline is intended as a **validation of the workflow** pending acquisition of real data.

---  

## Verification

To verify **the pipeline**:

```bash
# Run unit tests
pytest tests/unit/

# Run contract tests
pytest tests/contract/
```

All tests must pass before committing.
