# Quickstart: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

## Prerequisites
- Python 3.11+
- 2 CPU cores, 7 GB RAM, 14 GB disk (GitHub Actions Free Tier)
- Network access to HuggingFace (to load `oqmd/formation-energy`)

## Dataset Note
**CRITICAL**: This project uses the **OQMD Formation Energy** dataset.
- **Source**: `oqmd/formation-energy` on HuggingFace.
- **Access**: The pipeline loads this dataset programmatically via `datasets.load_dataset("oqmd/formation-energy")`.
- **No manual files required**: Do not provide local CSV files. The pipeline will fail if the HuggingFace source is unreachable.

## Installation

1. **Clone the repository** and navigate to the project root.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The entire pipeline (Training -> Evaluation -> Screening) can be run with a single command:

```bash
cd code
python main.py
```

### Configuration
Edit `config.yaml` to adjust:
- `seeds`: Random seed (default: 42).
- `splits`: Train/Val/Test ratios.
- `timeout`: Max runtime in hours (default: 5).
- `gp_inducing_points`: Number of inducing points for Sparse GP (default: 500).
- `risk_aversion`: Parameter $k$ for Expected Loss ranking in screening.

### Output
Results are saved in the `results/` directory:
- `calibration_report.csv`: ECE, Interval Score, Sharpness per method.
- `screening_results.csv`: Precision/Recall comparison (Expected Loss vs Point Prediction).
- `validation_report.json`: Log of excluded data rows.
- `uq_predictions.csv`: Full predictions with uncertainty intervals.

## Troubleshooting

### "SOURCE_UNREACHABLE: OQMD dataset not found"
- **Cause**: Network issue or HuggingFace source unreachable.
- **Fix**: Check network connectivity. No local file fallback is supported.

### "RuntimeError: GPU required"
- **Cause**: A library attempted to use CUDA.
- **Fix**: Ensure `torch` is installed with CPU support only (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).

### "GP Convergence Failed"
- **Cause**: Sparse GP optimization did not converge.
- **Fix**: The pipeline will log a warning and proceed with Deep Ensemble/MC-Dropout results only (GP excluded from ranking).

## Verification
Run the contract tests to ensure outputs match the schema:
```bash
pytest tests/contract/test_schemas.py
```