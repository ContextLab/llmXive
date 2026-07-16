# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-01-15

### Added
- Complete pipeline for grain boundary diffusivity prediction
- Data download from Materials Project and OpenKIM
- Geometry parsing with pymatgen integration
- XGBoost model training with hyperparameter tuning
- Cross-validation and bias testing
- SHAP interpretability analysis
- Sensitivity analysis across R² thresholds
- Comprehensive documentation (API reference, data schema, quickstart)

### Changed
- Updated data schema to include Rodrigues vector encoding
- Modified train/validation/test split to 70/15/15
- Added mutual information diagnostics for feature selection

### Fixed
- Memory constraints for 7GB RAM limit
- CPU-only execution for 2-core CI environments
- Data insufficiency error messaging

### Documentation
- Added API usage examples in README.md
- Created detailed data schema documentation
- Added threshold justification document
- Updated quickstart guide with troubleshooting
