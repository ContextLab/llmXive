# Quickstart: Comparing Born Model Predictions with Experimental Solvation Energies of Small Ions

**Branch**: `001-born-model-solvation-comparison` | **Date**: 2026-06-26

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Git (for repository access)

## Installation

```bash
# Clone repository and navigate to project
git clone <repository-url>
cd projects/PROJ-675-comparing-born-model-predictions-with-ex

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Data Preparation

```bash
# Download raw source data (NIST/CRC/Shannon)
# Note: URLs must be accessed via official APIs; if unavailable, manual compilation required
python code/data_compiler.py --compile --output data/experimental_solvation.csv

# Verify data integrity
python code/data_compiler.py --verify --input data/experimental_solvation.csv
```

## Running the Analysis

```bash
# Compile experimental dataset (Phase 1)
python code/data_compiler.py

# Compute Born predictions (Phase 2)
python code/born_calculator.py --input data/experimental_solvation.csv --output data/born_predictions.csv

# Run regression analysis (Phase 3)
python code/regression_analysis.py --predictions data/born_predictions.csv --experimental data/experimental_solvation.csv --output data/residual_analysis.csv

# Generate diagnostic plots (Phase 4)
python code/diagnostics.py --input data/residual_analysis.csv --output figures/
```

## Validation

```bash
# Run unit tests
pytest tests/unit/

# Run contract tests against schemas
pytest tests/contract/
```

## Expected Outputs

- `data/experimental_solvation.csv`: Compiled experimental dataset (≥30 ion-solvent pairs)
- `data/born_predictions.csv`: Born model predictions for all pairs
- `data/residual_analysis.csv`: Residuals and statistical analysis
- `figures/predicted_vs_experimental.png`: Scatter plot (FR-009a)
- `figures/residual_vs_radius.png`: Residual vs. ionic radius plot (FR-009b)
- `figures/residual_vs_dielectric.png`: Residual vs. dielectric constant plot (FR-009c)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| NIST/CRC API unavailable | Use manual compilation from published tables; document source in data/metadata.json |
| Missing ionic radius | Flag pair in data/experimental_solvation.csv; exclude from analysis |
| Experimental uncertainty missing | Set data_quality_flag to "uncertainty_missing"; include in SC-005 coverage calculation |
| RMSE > 20 kcal/mol | Flag for manual review; do not automatically exclude |
