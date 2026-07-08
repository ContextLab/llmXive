# Quickstart: Assessing Uncertainty Quantification Techniques

## Prerequisites

- Python +
- Git
- GitHub Actions Runner (or local machine with ≥2GB RAM)

## Installation

1. **Clone the repository** (or the specific feature branch):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-737-assessing-uncertainty-quantification-tec
   git checkout 001-assessing-uq-techniques
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins versions to ensure reproducibility.*

## Running the Pipeline

Execute the full workflow (Download -> Featurize -> Train -> Evaluate -> Stats):

```bash
python code/main.py
```

### Parameters
- `--dataset`: Optional. Specify a single dataset (e.g., `band_gap`) to skip others.
- `--method`: Optional. Run only a specific UQ method (e.g., `gpr`).
- `--max-samples`: Optional. Limit dataset size (default: a substantial number) to ensure RAM compliance.

## Expected Outputs

1. **Console**: Progress logs and any skipped method warnings.
2. **Files**:
   - `data/processed/`: Featurized datasets (CSV/Parquet).
   - `results/metrics.csv`: Per-method metrics (Calibration Error, Sharpness).
   - `results/stats_results.csv`: P-values for pairwise comparisons.
   - `results/sensitivity_conformal.csv`: Sensitivity analysis for Conformal Prediction.
   - `logs/execution.log`: Full execution log including errors.

## Troubleshooting

- **RAM Error**: If you encounter `MemoryError`, reduce `--max-samples` to 1000.
- **Dataset Missing**: If a specific property (e.g., Elastic Modulus) is missing, check `logs/execution.log` for the "Data Gap" warning. The pipeline will continue with available properties.
- **GPR Convergence**: If GPR fails, the pipeline logs the error and skips that method for the dataset.
