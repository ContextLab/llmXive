# Quickstart: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

## Prerequisites
- Python 3.11+
- `pip` or `conda`
- Access to a Unix-like environment (Linux/macOS/WSL)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd PROJ-372-assessing-sensitivity
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## Configuration

Create a `config.yaml` in the project root (or use the provided template):

```yaml
# Research Design Parameters
sample_size_tiers:
  - 10
  - 25
  - 50
  - 75
  - 90

num_subsets_per_tier: 200
convergence_threshold: 0.05  # 5%

# Random Seed
random_seed: 42

# Datasets (verified URLs)
datasets:
  - name: "census_income"
    url: "https://huggingface.co/datasets/jlh/uci-census-income-94/resolve/main/data/train-00000-of-00001-813c8c5127cc5484.parquet"
    target: "income"  # Example target column
    features: ["age", "education", "hours_per_week"] # Example features
  - name: "wine_quality"
    url: "https://huggingface.co/datasets/UCI/wine-quality-red/resolve/main/winequality-red.csv"
    target: "quality"
    features: ["fixed acidity", "volatile acidity", "citric acid", "residual sugar", "chlorides", "free sulfur dioxide", "total sulfur dioxide", "density", "pH", "sulphates", "alcohol"]
```

## Running the Pipeline

### 1. Ingest and Profile
Profiles the dataset for OLS assumption violations.
```bash
python -m src.cli main ingest --config config.yaml
```
*Output*: `artifacts/profiles/<dataset_id>_profile.json`

### 2. Resample and Fit
Generates subsets, fits OLS, computes subset-specific violations, and checks convergence.
```bash
python -m src.cli main resample --config config.yaml
```
*Output*: `artifacts/stability/subsets_*.json`, `artifacts/stability/coefficient_sd.json`, `artifacts/convergence.log`

### 3. Meta-Analysis
Runs the hierarchical regression analysis on stability results.
```bash
python -m src.cli main meta --config config.yaml
```
*Output*: `artifacts/meta_analysis/meta_results.json`

### 4. Generate Report & Visualizations
Compiles the final findings into a markdown report and generates **Stability Curves** (Coefficient SD vs. Subset Condition Number).
```bash
python -m src.cli main report --config config.yaml
```
*Output*: `reports/final_report.md`, `reports/stability_curves.png`

## Testing

Run unit tests:
```bash
pytest tests/unit -v
```

Run integration tests:
```bash
pytest tests/integration -v
```

## Troubleshooting

- **Memory Error**: Ensure `streaming=True` is used in `src/ingestion/loader.py` for large datasets.
- **Convergence Failed**: Check `artifacts/convergence.log`. If SE > 5%, the tier is marked "Invalid" and excluded from the final report. This is a validity gate, not a cosmetic log.
- **Missing Data**: Verify that the `target` and `features` columns exist in the dataset as defined in `config.yaml`.