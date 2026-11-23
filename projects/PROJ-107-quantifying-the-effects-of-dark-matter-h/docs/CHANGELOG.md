# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2023-10-27
### Added
- Initial project structure (`code/`, `data/`, `docs/`).
- Configuration management and logging infrastructure.
- TNG-100 data ingestion pipeline with chunked processing.
- Inertia tensor and shape metric calculations.
- Statistical analysis suite (mass-matching, tests, regression).
- Sensitivity analysis for binning thresholds.
- Alignment angle computation for halo-galaxy pairs.
- Comprehensive documentation (README, API, Design, Contributing).

### Changed
- Updated `requirements.txt` to include `black` and `ruff`.
- Added `.ruff.toml` and `pyproject.toml` for linting/formatting.

### Fixed
- Ensured all output CSVs include `associational_only=true` flag.
- Fixed pipeline runner to correctly aggregate and validate axial ratios.

## [0.1.0-alpha] - 2023-10-20
### Added
- Project skeleton and initial tasks.
- Basic data loader for TNG-100.

### Known Issues
- Millennium-II data fetch may fail if URL is unavailable (handled by gap logging).