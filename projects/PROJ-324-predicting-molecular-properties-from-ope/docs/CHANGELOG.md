# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **T038**: Documentation updates (`quickstart.md`, `research.md`, `api_reference.md`, `CHANGELOG.md`).
- **T039**: Explicit framing of findings as associational correlations.
- **T043**: Validation Protocol Summary with data provenance.
- **T045**: Conformational Sensitivity Analysis.

### Fixed
- **T036**: Batch-level timeout and retry mechanism for `obabel` subprocess.
- **T037**: Code cleanup, type hints, and docstrings.

### Changed
- **T021**: Statistical test now uses out-of-fold (OOF) predictions, not test set.
- **T031**: Runtime schema check for `measurement_uncertainty` and `quantity_of_substance`.

## [1.0.0] - 2026-06-27

### Initial Release
- Pipeline for predicting molecular properties using Open Babel fingerprints.
- Baseline (Crippen) vs. Random Forest comparison.
- SHAP-based explainability and stability analysis.
- Addressed reviewer concerns (Marie Curie, Rosalind Franklin).