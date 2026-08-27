# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T148** — declared artifact(s) missing/empty/invalid: code/analysis/run_pipeline.py
- **T004b** — The required file `code/download/knot_info_loader.py` does not exist, so there is no code to verify that it uses `retry_wrapper` or that the wrapper is invoked on failure. The deliverable is missing.
- **T151** — The provided `code/data/validator.py` is truncated and does not contain a complete implementation of `flag_dataframe` (the logic stops at an unfinished line). Additionally, the required unit test `tests/unit/test_validator_flag_logic.py` is absent, so there is no evidence that core invariants are correctly excluded from `missing_invariant_flags`. The task’s verification criteria are therefore unmet.
