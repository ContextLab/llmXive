# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Tractography confidence threshold sensitivity analysis (Phase 6)
- Automated associational language compliance checking
- Comprehensive documentation (README, quickstart, API, troubleshooting)
- Data completeness reporting
- Robustness report with explicit sensitivity tables

### Changed
- Updated LOO K-Means to ensure strict subject independence
- Modified correlation analysis to condition on normality (Pearson vs Spearman)
- Enhanced report generation to include tractography noise sensitivity section

### Fixed
- Fixed memory optimization for large cohorts
- Fixed exclusion logging to capture all failure modes
- Fixed FDR edge case handling

## [1.0.0] - 2026-06-26

### Added
- Initial release of llmXive network topology pipeline
- Structural graph metric calculation (global efficiency, clustering, modularity)
- Dynamic functional state extraction with sliding-window analysis
- Leave-One-Out (LOO) K-Means for statistical independence
- Structure-function correlation with FDR correction
- Sensitivity analyses (window length, graph density)
- Project structure and configuration setup
- Test suite for core functionality

### Security
- No known security issues

## [0.1.0] - 2026-06-20

### Added
- Project scaffolding
- Requirements file
- Basic configuration structure

[Unreleased]:
[1.0.0]:
[0.1.0]:
