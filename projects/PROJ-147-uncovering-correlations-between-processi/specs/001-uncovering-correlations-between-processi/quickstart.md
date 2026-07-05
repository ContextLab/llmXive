# Quickstart: Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

## Prerequisites

- Python 3.11+
- Docker (optional, for CI)
- Git

## Installation

1. Clone the repository and navigate to the feature branch:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-147-uncovering-correlations-between-processi
   git checkout 001-uncovering-correlations
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

### Option 1: Local Execution (Recommended for Development)

```bash
# Run the full pipeline (real data fallback → synthetic)
python code/main.py --mode full

# Generate synthetic data only
python code/main.py --mode synthetic --num-samples 150

# Train model on existing data
python code/main.py --mode train

# Predict on new data (provide new_processing.csv)
python code/main.py --mode predict --input new_processing.csv
```

### Option 2: Docker (Reproducibility)

```bash
# Build the Docker image
docker build -t texture-pipeline .

# Run the pipeline inside container
docker run --rm -v $(pwd)/data:/app/data -v $(pwd)/output:/app/output texture-pipeline python code/main.py --mode full
```

### Option 3: GitHub Actions (CI)

Push to the feature branch to trigger the CI workflow:
```yaml
# .github/workflows/ci.yml (auto-generated)
name: Run Texture Pipeline
on: [push]
jobs:
  pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run pipeline
        run: |
          pip install -r requirements.txt
          python code/main.py --mode full
```

## Expected Outputs

- `output/predictions.csv`: Predicted texture coefficients for test set.
- `output/new_predictions.csv`: Predictions for new input data (if provided).
- `output/evaluation_report.json`: R², MAE, RMSE per coefficient and alloy family.
- `output/importance_plot.png`: Permutation importance visualization.
- `output/pipeline.log`: Detailed logs of all steps, warnings, and errors.
- `models/trained_model.joblib`: Serialized model artifact.

## Troubleshooting

- **Missing Data**: If `Data quality insufficient` error occurs, check `output/pipeline.log` for missing percentage.
- **VIF Warning**: Features with VIF ≥ 5 are removed; review `pipeline.log` for details.
- **Out-of-Range Predictions**: Warnings logged; predictions still generated.
- **CI Failure**: Check GitHub Actions logs for resource limits (RAM/CPU) or missing data files.

## Next Steps

- Review `output/evaluation_report.json` for model performance.
- Inspect `output/importance_plot.png` to understand key drivers.
- For scientific validation, acquire real paired rolling-process/texture data.
