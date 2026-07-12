# Changelog

All notable changes to the llmXive Automated Science Pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-15

### Added

#### Project Setup
- Initial project directory structure (`code/`, `tests/`, `data/`, `docs/`)
- Python project initialization with core dependencies
- Linting (ruff) and formatting (black) configuration
- Comprehensive documentation (README, quickstart, architecture, contributing)

#### Data Generation (Phase 2)
- Deterministic seed pinning utility (`code/utils/seeds.py`)
- Seed pairing verification function for strict task-seed pairing
- Configuration loader with YAML schema support
- Synthetic ALE execution trace generator with ground truth labels

#### User Story 1: Automated Failure Mode Classification (Phase 3)
- ALE log parser for extracting environment state and agent actions
- Normalization protocol with exact 1e-6 float tolerance
- Task goal validator using deterministic regex-based template matcher
- Local LLM classifier using `llama-cpp-python` (Q4_K_M)
- State reconstruction validator with accuracy threshold (≥95%)
- Classification report generator with failure mode counts and proportions

#### User Story 2: Context Checkpointing Intervention (Phase 4)
- Context-checkpointing wrapper for state summary regeneration
- Summary compression heuristics (truncation and abstraction)
- CPU-only task runner with `llama-cpp-python` (Q4_K_M)
- Memory monitoring and timeout logging (7GB RAM, 6h limit)
- Baseline and intervention experiment execution

#### User Story 3: Statistical Significance & Reporting (Phase 5)
- McNemar's test implementation for paired binary outcomes (replaces Mixed-Effects Logistic Regression)
- Multiple-comparison correction (Bonferroni and FDR)
- Sensitivity analysis module testing N=1, N=3, and N=5
- Final report generator with p-values, pass rates, and sensitivity analysis

#### Testing Infrastructure
- Unit tests for statistical significance calculation
- Integration tests for sensitivity analysis output
- Contract tests for parser normalization
- Integration tests for classification accuracy on golden set

### Changed

- Updated FR-007 to use regex-based template matcher instead of local LLM for goal validation
- Updated FR-005 to use McNemar's test instead of Mixed-Effects Logistic Regression
- Updated T004b to include `verify_pairing` function for strict pairing
- Removed T030 (replaced by T004b and T015 integration)

### Fixed

- Fixed configuration loader to correctly parse `model_config` and `checkpoint_config` sections
- Fixed seed verification to return proper checksums
- Fixed state validation gate (T013b) to halt pipeline on accuracy < 95%

### Documentation

- Added comprehensive quickstart guide
- Created architecture documentation
- Added contributing guidelines
- Updated README with project overview and features
- Created changelog for version tracking

## [0.0.1] - 2024-01-01

### Added

- Initial project planning and specification
- User stories definition (US1, US2, US3)
- Task breakdown and dependency mapping
- Feature requirements (FR-001 through FR-009)

### Notes

This version represents the initial planning phase with no code implementation.