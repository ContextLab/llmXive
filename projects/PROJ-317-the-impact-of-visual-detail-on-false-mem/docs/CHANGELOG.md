# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- T040: Comprehensive documentation updates including:
 - `docs/README.md`: Project overview, structure, and usage instructions.
 - `docs/ethics/README.md`: Ethics documentation guide.
 - `data/ethics/informed_consent.md`: GDPR-compliant informed consent template.
 - `data/ethics/irb_placeholder.md`: IRB approval placeholder.
 - `docs/quickstart.md`: Step-by-step quickstart guide.
 - `docs/api.md`: Complete API reference for all modules.
 - `docs/CHANGELOG.md`: This changelog.

### Fixed
- T018: Implemented "skip and log" logic for manipulation failures in `code/stimuli/manipulator.py`. Errors are now logged to `data/logs/manipulation_errors.log`.

## [1.0.0] - Initial Release

### Added
- Project structure setup (T001-T004).
- Data loading utilities with mock dataset generation (T006).
- Power analysis implementation (T012).
- Entity classes for Image, Participant, and Response (T013, T014).
- Logging and configuration management (T008, T009).
- Ethics artifacts generation (T010).
- Image manipulation pipeline (enhanced/reduced detail) (T015-T017).
- Error handling for manipulation and data fetching (T018, T019, T021).
- Participant simulation interface and session management (T025-T031).
- Statistical analysis (ANOVA, Bonferroni) and visualization (T035-T039).
- CLI entry points for all major operations (T020, T031, T039).
- Unit and integration tests for all user stories (T011-T013, T022-T024, T032-T034).

### Changed
- Moved Power Analysis to Phase 2 (T012) to satisfy pre-data collection requirements.
- Fixed entity paths to `code/data/` to match plan.md.
- Added specific calibration parameters to T006 and false-detail logic to T027.
- Split error handling into separate tasks for fetching (T019) and manipulation metadata (T018).
- Renamed tasks to avoid ID collisions and improve clarity.

### Removed
- T011 (Cellular hypothesis) to eliminate scope creep.
- Redundant task definitions and ambiguous dependency text.