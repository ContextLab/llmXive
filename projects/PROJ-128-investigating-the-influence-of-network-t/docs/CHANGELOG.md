# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-06-26

### Added

- **Phase 1: Setup**
 - T001: Project directory structure (`code/`, `data/`, `contracts/`, `tests/`)
 - T002: `requirements.txt` with all dependencies
 - T003: Linting and formatting configuration

- **Phase 2: Foundational**
 - T004-T005: Configuration parameters (window length, K-Means K, density thresholds)
 - T006-T011: Data loading utilities, preprocessing skeletons, schema definitions

- **Phase 3: User Story 1 (MVP)**
 - T015: Structural graph metric calculation (global efficiency, clustering, modularity)
 - T016: Leave-One-Out (LOO) K-Means centroid generation
 - T017: LOO state assignment and dynamic metric calculation
 - T018-T020: Batch processing, aggregation, and exclusion logging
 - T012-T014: Unit and integration tests

- **Phase 4: User Story 2**
 - T024-T028: Normality testing, correlation analysis, FDR correction, and result generation

- **Phase 5: User Story 3**
 - T031-T035: Sensitivity analysis, resource monitoring, and final report generation

- **Phase N: Polish**
 - T050: Comprehensive documentation updates (`README.md`, `docs/README.md`, `docs/CHANGELOG.md`)

### Changed

- Updated task T016/T017 to implement strict LOO K-Means for statistical independence.
- Removed unapproved scope creep (Phase 6: Tractography Noise Sensitivity).

### Fixed

- Ensured all scripts write real output files to disk (no in-memory-only execution).
- Enforced "fail loudly" policy for data loading (no synthetic fallbacks).

### Known Issues

- None reported at this time.
