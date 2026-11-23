# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Full documentation suite (`docs/ARCHITECTURE.md`, `docs/USER_GUIDE.md`, `docs/CONTRIBUTING.md`).
- Enhanced `README.md` with installation, usage, and troubleshooting sections.
- Automated reproducibility report generation (`code/utils/metrics.py`).
- Freedman-Lane permutation test implementation.
- k-fold cross-validation for model robustness.

### Changed
- Refactored data ingestion to enforce hard gates (Phase 0).
- Updated centrality calculation to use full AAL3 atlas (~90 regions).
- Improved memory efficiency with `float32` enforcement and batch processing.

### Fixed
- Fixed retention rate calculation to correctly log exclusions.
- Resolved VIF logic to correctly switch between Global and PCA models.
- Corrected output paths for behavioral metrics and centrality scores.

## [0.1.0] - 2023-10-27

### Added
- Initial project setup.
- Data download and preprocessing pipeline.
- Basic centrality calculation.
- Linear regression model.
- Unit and integration tests.

### Changed
- Migrated from sample tasks to real implementation tasks.
- Updated dependencies to latest versions.

### Removed
- Placeholder data and synthetic datasets.

## [0.0.1] - 2023-09-01

### Added
- Project scaffolding.
- Initial `tasks.md` and `plan.md`.