# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- T036: Complete documentation suite including:
 - `docs/quickstart.md`: Step-by-step pipeline execution guide
 - `docs/research_methodology.md`: Scientific methodology documentation
 - `docs/data_dictionary.md`: Complete data field definitions
 - `docs/implementation_guide.md`: Developer implementation guide
 - `docs/CHANGELOG.md`: This changelog

### Changed
- Updated documentation to reflect current pipeline state
- Added troubleshooting sections to quickstart guide

### Fixed
- Documentation paths now match actual project structure
- All output file paths verified against actual implementations

## [1.0.0] - 2024-01-15

### Added
- Complete data acquisition pipeline (GitHub scraper, synthetic generator)
- Feature extraction modules (complexity, timestamps, style, semantic similarity)
- Propensity score matching implementation
- Statistical testing framework (t-test, Mann-Whitney)
- Sensitivity analysis across star-count quartiles
- Visualization generation (box plots, CDF curves)
- Prompt-based cohort validation
- Comprehensive testing suite (contract, integration, unit tests)
- Docker environment for replication

### Changed
- Merged T008 and T013 into single task T013
- Reorganized tasks by user story for independent implementation
- Implemented mandatory generation with halt-on-failure for T014b and T033

### Removed
- Sample tasks from initial tasks.md template
- Placeholder code and TODO stubs

### Security
- PII scanning enforcement added
- Rate limiting with exponential backoff implemented
- API token validation added

## [0.1.0] - 2023-12-01

### Added
- Initial project structure
- Setup tasks (T001a-T001d)
- Foundational infrastructure (T002-T008, T013)
- Basic configuration and validation utilities

### Changed
- Initial task list creation based on user stories
- Project directory structure established

## [0.0.1] - 2023-11-01

### Added
- Project inception
- Initial requirements gathering
- Specification documents created

[Unreleased]:
[1.0.0]:
[0.1.0]:
[0.0.1]: 