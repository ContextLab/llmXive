# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and documentation.
- Deterministic synthetic tensor generator.
- High-precision reference engine using `decimal`.
- Dynamic compilation and execution framework.
- Statistical analysis (Welch's t-test, block averaging).
- Stability checking (L2 error, Max Diff).
- Pareto frontier visualization.
- Comprehensive documentation suite.

### Changed
- Updated statistical method from "paired t-test" to "Welch's Independent Samples t-test" for correctness.
- Clarified stability threshold (error > 1e-5) for exclusion from final results.
- Fixed iteration count to 1000 (Constitution Principle VII).

### Fixed
- Memory pressure handling: Auto-downsampling from 768x768 to 512x512.
- NaN detection and exclusion logic.

## [0.1.0] - 2023-10-27

### Added
- Initial release.
- Core functionality for benchmarking compiler optimizations.
- Documentation for setup, usage, and API reference.
