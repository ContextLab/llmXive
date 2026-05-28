# Spec — synthetic seed (calibration positive)

## User Story
US1: As a maintainer I want a calibration verdict per panel so I can
target prompt adjustments.

## Functional Requirements
- FR-001: System should emit one calibration verdict per injector run.
- FR-002: System should persist the adjudication checklist to disk for
  the maintainer to review.

## Success Criteria
- SC-001: 100% of injections in the calibration set produce a verdict
  (no silent drops), measured by `tests/unit/test_differential_calibration.py`.
