# Quick Start Guide

## 1. Setup Environment
```bash
python -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Generate Synthetic Data (for Validation)
```bash
python code/generate_synthetic_data.py --output data/raw/synthetic_test_data.csv
```

## 3. Run Full Pipeline
```bash
python code/main.py \
 --input data/raw/synthetic_test_data.csv \
 --output data/results/ \
 --allow-synthetic-fallback
```

## 4. Verify Results
```bash
# Check integrity of all artifacts
python scripts/verify_integrity.py

# Validate statistical and causal compliance
python scripts/final_validation.py

# Review power and sensitivity
python scripts/review_power_sensitivity.py
```

## 5. View Outputs
- **Significance Summary**: `data/results/significance_summary.md`
- **Final Report**: `data/results/final_report.md`
- **Correlation Results**: `data/results/correlation_results.csv`

## Notes
- Use `--allow-synthetic-fallback` only for local validation.
- For real data, ensure `data/candidates/verified_sources.yaml` is populated and remove the fallback flag.
