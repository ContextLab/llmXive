# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — declared artifact(s) missing/empty/invalid: src/data_loader.py
- **T013** — declared artifact(s) missing/empty/invalid: src/qc.py
- **T014** — declared artifact(s) missing/empty/invalid: src/qc.py, data/processed/subject_qc_list.json
- **T015** — declared artifact(s) missing/empty/invalid: src/qc.py
- **T016** — declared artifact(s) missing/empty/invalid: src/qc.py
- **T017** — declared artifact(s) missing/empty/invalid: src/main.py, data/processed/subjects_metadata.json
- **T009** — The provided `tests/unit/test_qc.py` contains only tests for `verify_conditions` and does not include a stub for `test_motion_calculation` with the required signature or `NotImplementedError` assertion. Additionally, the required source file `src/qc.py` (which should define `calculate_motion`) is missing entirely. Consequently, the task’s deliverables are not present.
- **T010** — The provided `tests/unit/test_qc.py` contains only tests for `verify_conditions`; there is no stub for `test_motion_hard_stop` nor any reference to `check_subject_count`. Moreover, `src/qc.py` is missing entirely, so the required function signature cannot be matched. The task’s required artifacts are absent.
- **T011** — The `tests/unit/test_qc.py` file exists but its contents do not assert a `NotImplementedError` as required and instead expect real behavior from `verify_conditions`. Moreover, the referenced `src/qc.py` (which should contain the `verify_conditions` signature) is missing entirely. Both the stub behavior and the required source file are absent.
- **T023** — declared artifact(s) missing/empty/invalid: src/preprocessing.py
- **T024** — declared artifact(s) missing/empty/invalid: src/extraction.py
