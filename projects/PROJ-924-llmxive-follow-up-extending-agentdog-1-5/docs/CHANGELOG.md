# Changelog

All notable changes to the llmXive Drift Detection project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure for `PROJ-924-llmxive-follow-up-extending-agentdog-1-5`.
- Documentation directory (`docs/`) with README, Quickstart, Data Model, API, Architecture, Contributing, and CHANGELOG.
- Setup tasks (T001-T006) for directory creation.
- Requirements file with core dependencies.

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [0.1.0] - 2023-10-27

### Added
- Initial commit for the llmXive Follow-up project.
- Basic directory structure (code, tests, data, specs).
- Configuration management (`config.py`).
- Data loading utilities (`data_loader.py`).
- Taxonomy building utilities (`taxonomy_builder.py`).
- Drift scoring logic (`drift_scoring.py`).
- Validation and annotation interfaces (`validation.py`, `annotator_interface.py`).

### Changed
- Replaced `gpt-4o-mini` with `facebook/bart-large-mnli` for baseline comparison to ensure CPU-only reproducibility.

### Fixed
- Memory limits enforced in batch processing (< 7GB RAM).
- Checksum verification for raw data integrity.

### Security
- Implemented blinding of drift scores before human annotation to prevent bias.
- Added inter-annotator agreement (Kappa) checks to ensure data quality.

[Unreleased]:
[0.1.0]:
