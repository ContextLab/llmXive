# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T102** — Requested task execution failed; rerun successfully: code/data/run_fetch.py exit=1
- **T103** — The recorded pytest run of `code/tests/unit/test_filter_subjects.py` FAILED (exit 1): the test asserts `participant.fmri_path == fmri_004` but `filter_subjects` returns a toolkit-resolved absolute path while the test builds a relative one, so the single test covering all three exclusion codes does not pass. Additionally, the required output `data/interim/included_subjects.csv` does not exist, and the exclusion log contains only unrelated `FILE_NOT_FOUND`/SYSTEM entries rather than the MISSING_SCAN/MISSING_SCORE/HIGH_MOTION rows the tests should have produced — fix the path comparison (e.g., re
- **T104** — Requested task execution failed; rerun successfully: code/data/run_preprocess.py exit=-1 (TIMEOUT)
