# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The `data/raw/assistments.csv` file (and its checksum) is absent, and the provided script does not use `streaming=True` nor emit the exact required timeout error message (“ERROR: Failed to download … within 300 seconds – aborting pipeline.”). Consequently the deliverables and core requirements are not satisfied.
- **T012c** — declared artifact(s) missing/empty/invalid: code/download/fetch_khan_academy.py, data/raw/khan_academy.csv
- **T012a** — The script `code/download/validate_assistments_data.py` exists but is incomplete (truncated) and relies on `contracts/problem.schema.yaml`, which is missing from the repository, so it cannot actually validate the dataset or produce the required error messages. The necessary schema file must be added and the script finished for the task to be considered complete.
- **T012b** — declared artifact(s) missing/empty/invalid: code/download/verify_timeout_handling.py
