# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `src/data/download.py` script correctly handles downloading, retry logic, column mapping, deterministic sampling, checksum logging, and output files, and the log shows ≥150 valid snippets. However, the docstring validation function `_is_valid_docstring` does **not** enforce the required “≥ 5 tokens” rule, so the validation step is incomplete. Additionally, there is no provided evidence that the pytest `src/tests/test_download.py` was executed and passed. The implementation must be updated to count tokens (e.g., `len(doc.split()) >= 5`) and the test suite results need to be shown.
- **T004** — Requested task execution failed; rerun successfully: src/utils/validate_environment.py exit=1
