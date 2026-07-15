# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Complete documentation suite (README.md, docs/)
- API reference documentation
- Usage guide with examples
- Contributing guidelines
- Design decisions documentation (ADRs)
- Changelog file

### Changed
- Updated configuration to use dynamic dataset discovery
- Optimized permutation count for clustering coefficient on large datasets
- Enhanced error handling with fail-loudly policy

### Fixed
- Data hygiene pipeline to properly exclude constant variables
- BY correction implementation for multiple testing
- Threshold sensitivity sweep to include 0.1 baseline

## [0.1.0] - 2024-02-10

### Added
- Initial project structure (T001-T003)
- Configuration management system (T004)
- Dynamic dataset discovery (T004b, T017)
- UCI data loading and hygiene pipeline (T005-T006)
- Statistical engine with correlation computation (T007, T012)
- Graph construction and network statistics (T013-T014)
- Benjamini-Yekutieli correction (T008, T018-T020)
- Visualization module (T009, T025-T026)
- Permutation testing engine (T015)
- Synthetic validation framework (T016, T016b)
- Threshold sensitivity analysis (T024, T027)
- Primary threshold visualizations (T025b)
- Main pipeline orchestration (T021, T022, T028)
- Unit and integration tests (T010-T011, T018, T023)

### Changed
- N=1,000 permutations (optimized from N=2,000)
- Threshold sweep: {0.1, 0.2, 0.3, 0.4, 0.5}
- BY procedure as primary correction method

### Security
- Fail-loudly policy for data loading (Constitution VII)
- Data integrity verification with checksums (Constitution I)

## [0.0.1] - 2024-01-15

### Added
- Project initialization
- Initial task tracking (tasks.md)
- Design documents in specs/