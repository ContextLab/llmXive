<!-- INJECTED CALIBRATION FLAW: FR-999 declared in spec but NO task in this file references it. The coverage lens should flag this as a REQUIREMENT-class concern. -->

# Tasks — synthetic seed (calibration positive)

- [ ] T001 [FR-001]: System MUST emit one calibration verdict per
  injector run. Implementation in `calibration/differential.py`.
  Verification: `tests/unit/test_differential_calibration.py::
  test_calibration_run_caught_when_expected_lens_in_injected_concerns`.

- [ ] T002 [FR-002]: System MUST persist the adjudication checklist
  to disk for the maintainer to review. Implementation: write the
  `to_markdown()` output to `specs/015-pipeline-convergence-protocol/
  calibration/adjudication-<domain>.md`. Verification:
  `tests/unit/test_differential_calibration.py::
  test_adjudication_report_markdown_includes_every_run_section`.
