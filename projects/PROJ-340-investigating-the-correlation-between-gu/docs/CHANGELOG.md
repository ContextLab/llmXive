# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Full pipeline implementation for gut microbiome-sleep correlation.
- Strict real-data mode with fail-loud behavior.
- Compositional data handling (CLR, SparCC).
- Causal language scanning in reports.
- Comprehensive documentation (README, quickstart, architecture, etc.).

### Fixed
- Fixed circular import in `main.py` and `run_stress_test.py`.
- Fixed missing output files in pipeline execution.
- Fixed schema validation errors.

### Changed
- Updated `requirements.txt` with pinned versions.
- Refactored `ingest.py` to support both real and synthetic modes.
- Improved error messages for missing variables.

## [1.0.0] - 2026-07-31

### Initial Release
- Project structure and setup (T001-T002).
- Schema definition and validation (T004).
- Data ingestion and outlier detection (T012-T014).
- Correlation analysis and FDR (T020-T025).
- Diagnostics (VIF, Power, Sensitivity) (T078, T080, T121-T122).
- Report generation and causal language guard (T087, T124).
- Integration tests and verification (T110-T113, T130-T132).

## [0.1.0] - 2026-07-30

### Planning
- Initial design documents.
- Task breakdown.
- API surface definition.