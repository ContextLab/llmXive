# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **T031**: Comprehensive documentation update including `README.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, and `CHANGELOG.md`.
- **T036**: Formal `amendment.md` documenting Methodology Overrides (N < 130 power constraint and unconditional robustness check).
- **T034**: Unit tests for `config.py` seed verification and `robustness.py` conditional logic.

### Changed
- Updated `README.md` to reflect the "Fail Loud" data hygiene principle and specific pipeline execution steps.
- Refined `ARCHITECTURE.md` to detail the data flow and component responsibilities.

### Fixed
- Ensured all documentation artifacts are present in the repository root and `docs/` directory.

## [1.0.0] - Initial Release
- Implemented core pipeline: Ingestion, Cleaning, Modeling, Robustness, and Reporting.
- Established project structure and configuration management.
- Integrated statistical power constraints and construct validity checks.
