# Changelog

## [Unreleased]
- Added documentation updates for T038.
- Implemented `quickstart.md` with detailed instructions.
- Added `docs/` directory with comprehensive guides.

## [1.0.0] - 2023-10-27
### Added
- Initial implementation of the pipeline.
- Data ingestion from OSF/HF.
- VAD inference for prime valence.
- LMM modeling with retry logic.
- Report generation with limitations section.

### Changed
- Critical Design Change #2: Human-rated ambiguity is now mandatory.
- Critical Design Change #3: All findings are framed as associational.
- Critical Design Change #4: Linkage integrity is strictly enforced.

### Fixed
- Fixed PII scanning to detect leaks in processed data.
- Fixed chunked processing for large datasets.

## [0.1.0] - 2023-10-01
### Added
- Project setup and directory structure.
- Basic configuration and state management.