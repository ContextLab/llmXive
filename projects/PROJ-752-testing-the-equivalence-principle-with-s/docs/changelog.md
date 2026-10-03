# Changelog

All notable changes to the Equivalence Principle testing pipeline are documented in this file.

## [Unreleased]

### Added
- T042: Comprehensive documentation (README, API reference, implementation notes, user guide, changelog)
- T045: Unit tests for edge cases (missing data, empty results)
- T046: Quickstart validation script and reproducibility report

### Changed
- Improved error messages for memory limit exceeded
- Enhanced logging format for better readability
- Updated benchmark value handling to be more graceful

### Fixed
- Fixed issue with missing benchmark value raising FileNotFoundError
- Corrected mean orbital radius calculation in T025
- Resolved sensitivity analysis plot generation issues

## [1.0.0] - 2024-01-15

### Added
- Initial release of the Equivalence Principle testing pipeline
- Full data ingestion from ILRS archive
- Separate and joint least-squares orbit determination
- Eötvös parameter estimation with 95% confidence intervals
- Sensitivity analysis across geopotential models
- Statistical validation (F-test, BIC, multiple comparison correction)
- Resource monitoring (memory, time)
- Feasibility gap reporting

### Implemented Phases
- Phase 1: Setup (T001-T003)
- Phase 2: Research Prerequisites (T048.0a-T048.0d)
- Phase 3: Foundational (T004-T010, T023a, T007a, T009a-T009c)
- Phase 4: User Story 1 (T011-T019, T009)
- Phase 5: User Story 2 (T020-T028, T023b-T023e, T024a, T024, T025, T025a)
- Phase 6: User Story 3 (T029-T037, T032a-T032f, T033a-T033c, T034-T036, T049)
- Phase 7: User Story 4 (T038, T040, T041)
- Polish: T043, T044

### Known Limitations
- Single-arc fitting (no multi-arc combination)
- Simplified SRP model (cannonball)
- Limited geopotential models (GGM05C, EGM2008, GOCO)
- No tides modeling (solid Earth, ocean)
- CPU-only execution (no GPU support)

### Dependencies
- Python 3.9+
- numpy, scipy, pandas
- astropy
- requests, psutil
- pyyaml

## [0.1.0] - 2023-12-01

### Added
- Project structure and initial configuration
- Basic data ingestion framework
- Schema definitions for NormalPoint, OrbitSolution, EotvosResult

### Changed
- Renamed project to PROJ-752-testing-the-equivalence-principle-with-s

---

## Versioning Scheme

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

## Release Notes

For detailed release notes, including migration guides and breaking changes, please refer to the project documentation.

## Contributors

- Primary implementer: LLM-driven implementer for llmXive
- Reviewers: Science team
- Maintainer: PROJ-752 project lead