# Changelog

## [Unreleased]

### Added
- Full documentation suite (README, ARCHITECTURE, USER_GUIDE, CONFIGURATION, TESTING, CONTRIBUTING, FAQ, REPRODUCIBILITY, CHANGELOG).
- Comprehensive project structure and pipeline documentation.

### Changed
- Clarified "valid" configurations as "stable" in Pareto frontier plots.
- Updated statistical method to Welch's Independent Samples t-test.

### Fixed
- Memory pressure handling with automatic downscaling.
- NaN detection and exclusion from statistical analysis.

## [1.0.0] - Initial Release

### Features
- C++ kernel compilation and execution with various optimization flags.
- High-precision reference calculation using Python `decimal` module.
- Numerical stability analysis with L2 error and max diff.
- Statistical significance testing with Welch's t-test.
- Pareto frontier visualization for latency vs. error trade-offs.
- Full reproducibility with SHA-256 manifest generation.

### Infrastructure
- Project structure setup with modular components.
- Configuration management for flags and dimensions.
- Logging infrastructure for audit and debugging.
- Test suite for unit and integration validation.

### Known Issues
- Memory pressure may cause automatic downscaling (documented behavior).
- Compiler availability required for execution.