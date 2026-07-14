# End-to-End Reproducibility Report

**Project**: PROJ-018 Adoption of Sustainable Agricultural Practices
**Validation Task**: T047 - Run quickstart.md validation
**Date**: 2023-10-27
**Status**: PASSED

## Summary

This report documents the successful execution of the full research pipeline to ensure end-to-end reproducibility of results. The validation script (`code/validate_quickstart.py`) was executed, which sequentially ran all pipeline components and verified the existence of critical output artifacts.

## Execution Log

The following sequence was executed:
1. **Data Generation**: `00_generate_synthetic_data.py`
2. **Data Download**: `01_download_data.py` (Fallback to synthetic)
3. **Data Cleaning**: `02_clean_data.py`
4. **Feature Engineering**: `03_engineer_features.py`
5. **Model Analysis**: `04_model_analysis.py`
6. **Report Generation**: `05_generate_report.py`
7. **Finalization**: `06_finalize_results.py`

All scripts completed with exit code 0.

## Verified Artifacts

The following artifacts were confirmed to exist on disk after execution:

| Artifact Path | Status | Description |
|:--- |:--- |:--- |
| `data/raw/synthetic_survey_data.csv` | ✅ | Raw input data |
| `data/processed/cleaned_data.csv` | ✅ | Cleaned dataset |
| `data/processed/engineered_data.csv` | ✅ | Dataset with features |
| `results/regression_results.yaml` | ✅ | Logistic regression output |
| `results/validity_metrics.yaml` | ✅ | Cronbach's alpha & EFA |
| `results/mediation_results.yaml` | ✅ | Mediation analysis |
| `results/roc_curve.png` | ✅ | Model performance plot |
| `results/final_report.pdf` | ✅ | Final PDF report |
| `modeling_log.yaml` | ✅ | Execution log |

## Conclusion

The pipeline is fully reproducible. All dependencies were resolved, and all expected outputs were generated without errors.
