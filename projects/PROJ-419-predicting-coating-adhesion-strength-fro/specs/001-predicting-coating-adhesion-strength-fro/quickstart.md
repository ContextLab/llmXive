# Quickstart: Predicting Coating Adhesion Strength from Composition and Surface Features

## Prerequisites

- Python 3.11+
- pip (package manager)
- Git (for repository access)
- GitHub Actions account (for CI/CD)

## Installation

1. **Clone the Repository**:
 ```bash
 git clone
 cd coating-adhesion-prediction
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 **requirements.txt** (example):
 ```text
 pandas>=2.0.0
 scikit-learn>=1.3.0
 shap>=0.43.0
 requests>=2.31.0
 numpy>=1.24.0
 pyyaml>=6.0.0
 pytest>=7.4.0
 ```

## Data Setup

### Step 1: Obtain Verified Datasets

**CRITICAL**: The project requires verified URLs for:
- Materials Project API
- NIST Surface Metrology Repository
- Open-access literature sources (adhesion data)

**Current Status**: No verified URLs are provided in the `# Verified datasets` block.
- **Action**: You must obtain these URLs before proceeding.
- **Mock Data**: For testing purposes, you may use mock data (see `data/mock/`), but this is **not** for final results. The pipeline will halt if mock data is used in production mode.

### Step 2: Place Raw Data

1. Download raw data (once URLs are verified) and place in:
 ```
 data/raw/materials_project/
 data/raw/nist_surface/
 data/raw/literature/
 ```

2. Ensure files are in CSV/JSON format as expected by `ingestion.py`.

### Step 3: Run Ingestion Pipeline

```bash
python code/ingestion.py --input-dir data/raw --output data/processed/coating_adhesion_dataset.csv
```

**Output**:
- `data/processed/coating_adhesion_dataset.csv` (unified dataset)
- `data/processed/logs/ingestion.log` (exclusion/deduplication logs)

## Modeling & Analysis

### Step 1: Run Full Pipeline

```bash
python code/main.py
```

This script will:
1. Ingest data (if not already done).
2. Preprocess and engineer features.
3. Train models (GBR, RFR) with nested CV.
4. Compute SHAP values and permutation importance.
5. Compare with baselines (composition-only, surface-only).
6. Output results to `data/processed/`.

### Step 2: Inspect Results

- **Model Performance**: `data/processed/model_results.json`
- **Feature Rankings**: `data/processed/feature_rankings.json`
- **SHAP Plots**: `data/processed/shap_plots/` (if generated)
- **Baseline Comparison**: `data/processed/baseline_comparison.json`

### Step 3: Validate

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

## GitHub Actions CI/CD

### Configuration

The project includes a `.github/workflows/pipeline.yml` file that:
1. Checks out the code.
2. Sets up Python 3.11.
3. Installs dependencies.
4. Runs the pipeline (or a subset for testing).
5. Validates results against contracts.

### Manual Trigger

```bash
# Push to branch
git push origin 001-predicting-coating-adhesion

# Or trigger manually via GitHub UI
```

### Expected Runtime

- **Ingestion**: <30 minutes (depending on data size).
- **Modeling**: <2 hours (for [deferred] rows, nested CV).
- **Total**: <4 hours (within 6-hour limit).

## Troubleshooting

### Issue: "No verified dataset URLs found"

**Solution**: Obtain verified URLs for Materials Project, NIST, and literature sources. Update `research.md` and the ingestion script with these URLs.

### Issue: "Memory limit exceeded"

**Solution**:
- Ensure dataset is sampled to ≤5,000 rows.
- Use chunked processing in `ingestion.py`.
- Check `data/processed/logs/ingestion.log` for exclusion counts.

### Issue: "API rate limit hit"

**Solution**:
- The script includes exponential backoff (3 retries).
- If still failing, reduce request frequency or cache responses.

### Issue: "SHAP takes too long"

**Solution**:
- Use `shap.TreeExplainer` for tree-based models (faster than KernelExplainer).
- Limit SHAP to top 10 features.
- Use `approximate=True` if available.

### Issue: "Data Alignment Failed"

**Solution**:
- The pipeline will reject records that cannot be linked via unique identifiers.
- Check `data/processed/logs/validation.log` for details on rejected records.
- If too many records are rejected, the project may halt due to insufficient sample size.

## Next Steps

1. **Verify Datasets**: Obtain and validate URLs for required data sources.
2. **Run Full Pipeline**: Execute `code/main.py` with real data.
3. **Review Results**: Analyze `model_results.json` and `feature_rankings.json`.
4. **Write Paper**: Draft the paper section, citing results from `data/processed/`.
5. **Submit**: Advance to `research_complete` stage after validation.

## Contact

For issues or questions, open an issue in the repository or contact the project maintainer.