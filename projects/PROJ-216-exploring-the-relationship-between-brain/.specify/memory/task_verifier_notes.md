# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — declared artifact(s) missing/empty/invalid: data/.verify_structure.log
- **T008a** — The required file `specs/amendment-001-fluid-intelligence-n10.md` was not presented, and no content showing the three amendment clauses was provided. Without the artifact, the task cannot be considered fulfilled.
- **T008b** — No evidence of a file at `specs/amendment-002-sc-n10-baseline.md` was provided, nor any content showing the required redefinition of SC-001 and SC-005 to N=10. The implementer must supply the actual markdown file with the specified baseline revisions.
- **T009** — The `ResourceMonitor` class in `code/utils.py` is truncated and its `finalize` method does not fully implement JSON writing (the code ends mid‑dictionary). The expected `resource_profile.json` file is absent, and the unit test `tests/unit/test_resource_monitor.py` is also truncated before it asserts the JSON schema, so it does not actually verify the file’s contents. The required implementation and complete test are missing.
- **T016c** — declared artifact(s) missing/empty/invalid: data/processed/validation_errors.log
- **T018a** — declared artifact(s) missing/empty/invalid: data/processed/motion_exclusion_log.csv
- **T018b** — declared artifact(s) missing/empty/invalid: data/processed/motion_exclusion.log
- **T019a** — declared artifact(s) missing/empty/invalid: data/processed/preprocessing_stats.json
- **T019b** — No `preprocessing_stats.json` file (or any evidence of its creation) is present, and there is no code or output showing the calculation of `successful_subjects / total_downloaded_subjects`. Consequently, the required artifact is missing, so the task is not satisfied.
