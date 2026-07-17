# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2023-10-27

### Added
- **Initial Pipeline Implementation**:
 - Data acquisition and stratified sampling (`download_data.py`).
 - Code generation with retry logic (`generate_code.py`).
 - Metric analysis (Complexity, Coverage, Pass Rate) (`analyze_metrics.py`).
 - Statistical testing suite (Wilcoxon, McNemar, Fisher, Permutation) (`statistical_tests.py`).
 - Report generation with visualizations (`report_generator.py`).
- **Sensitivity Analysis**: Support for CodeLlama-3B/7B models via local quantization and API fallback.
- **Integrity Verification**: SHA256 checksums for all artifacts (`artifact_manager.py`).
- **Logging**: Comprehensive logging infrastructure with task ID tracking.
- **Documentation**:
 - `README.md`: Project overview and quick start.
 - `docs/RESEARCH_PROTOCOL.md`: Scientific methodology.
 - `docs/API_REFERENCE.md`: Module API documentation.
 - `docs/ARCHITECTURE.md`: System design and data flow.
 - `docs/CHANGELOG.md`: This file.

### Changed
- Updated `code/requirements.txt` to include `radon`, `pytest-cov`, `jinja2`, `matplotlib`, `datasets`, `transformers`, `accelerate`, `scipy`, `pandas`.
- Refactored `code/utils.py` for better logging and hashing utilities.

### Fixed
- Resolved issue where coverage metrics were not recorded if test execution failed (now marked as `[deferred]`).
- Fixed stratified sampling logic to ensure exact sample size of 50.

### Security
- Ensured all API keys are loaded from environment variables.
- Added citation validation step to prevent hallucinated references in reports.

## [0.1.0] - 2023-10-20

### Added
- Project structure and initial task definitions.
- Basic directory setup (`data/`, `results/`, `state/`).
- `code/validate_quickstart.py` for pipeline validation.