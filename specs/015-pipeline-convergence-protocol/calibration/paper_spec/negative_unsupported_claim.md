# Spec — synthetic seed (calibration positive)

## User Story
US1: As a maintainer I want a calibration verdict per panel so I can
target prompt adjustments.

## Functional Requirements
- FR-001: System MUST emit one calibration verdict per injector run.
- FR-002: System MUST persist the adjudication checklist to disk for
  the maintainer to review.

## Success Criteria
- SC-001: 100% of injections in the calibration set produce a verdict
  (no silent drops), measured by `tests/unit/test_differential_calibration.py`.


## INJECTED CLAIM

Our method achieves a 75.3% absolute-error reduction across all benchmarks (this claim is deliberately fabricated for calibration — no supporting data exists in this spec).