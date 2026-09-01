# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-06-26

### Added
- Complete implementation of the research pipeline for investigating network topology influence.
- Leave-One-Out (LOO) K-Means state extraction to ensure statistical independence.
- Structural graph metric calculation (global efficiency, clustering, modularity).
- Dynamic functional metric calculation (dwell time, visited states).
- Correlation analysis with Benjamini-Hochberg FDR correction.
- Robustness analysis for window length and density threshold variations.
- Comprehensive documentation in `docs/` directory.
- Associational language audit and framing in reports.

### Changed
- Removed unapproved scope creep (Phase 6: Tractography Noise Sensitivity).
- Updated research question validation to emphasize associational framing.

### Fixed
- Ensured all data loaders fail loudly on missing real data (no synthetic fallbacks).
- Corrected LOO implementation to strictly exclude the current subject from centroid generation.

### Documentation
- Added `docs/README.md`, `docs/ARCHITECTURE.md`, `docs/PROCESS.md`, and `docs/CHANGELOG.md`.
- Updated root `README.md` with quick start guide and key methodological notes.

## [0.1.0] - 2026-06-25

### Added
- Initial project setup and directory structure.
- Basic configuration and schema definitions.
- Skeleton modules for preprocessing and analysis.

### Notes
- This version was a foundational setup to enable subsequent user story implementations.