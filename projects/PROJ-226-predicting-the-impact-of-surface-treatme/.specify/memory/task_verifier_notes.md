# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The script `code/verify_data_source.py` runs and creates `data/source/availability_report.json`, but the JSON contains `"datasets": []`, meaning no openly downloadable dataset with all required variables was found. Moreover, the test `tests/test_verify_data_source.py` expects the report at a temporary location and fails because the script writes to the project path, so the CI check does not detect the empty list as a failure. The core requirement—verifying that at least one suitable dataset exists—is not met.
- **T002** — Requested task execution failed; rerun successfully: code/download_data.py exit=1
