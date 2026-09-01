# Quick Start Guide

This guide explains how to run the pipeline and verify artifacts for PROJ-006.

## Prerequisites

- Python 3.9+
- `pip install -r requirements.txt`

## 1. Verify Spec and Plan

Run the validation scripts to ensure the design documents are complete.

```bash
python scripts/validate_spec_todos.py
python scripts/verify_hypothesis.py
python scripts/verify_novelty.py
```

## 2. Run the Pipeline (Synthetic Fallback for Testing)

To test the pipeline without real data, use the synthetic generator fallback.
This will generate `data/processed/analysis_dataset.csv` and other artifacts.

```bash
export CI=true
python src/cli/run_pipeline.py --stage full
```

**Note**: If real data is available in `data/raw/`, the pipeline will use it automatically.
If `CI=true` and no real data exists, the synthetic generator is invoked.

## 3. Validate Data Artifacts

After the pipeline runs, validate the generated artifacts against their schemas.

```bash
# Validate the main analysis dataset
python src/cli/validate.py data/processed/analysis_dataset.csv --schema-type dataset

# Validate regression results (if generated)
python src/cli/validate.py data/processed/regression_results.json --schema-type regression
```

## 4. Run Tests

Run the full test suite to ensure correctness.

```bash
pytest
```

## 5. Generate Final Report

Once analysis is complete, generate the final report.

```bash
python src/analysis/sensitivity_check.py
python src/services/report_generator.py
```

The report will be saved to `reports/final_report.pdf`.
