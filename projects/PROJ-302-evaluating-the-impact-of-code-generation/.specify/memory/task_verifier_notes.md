# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The three `<owner>_<repo>.parquet` files and `commit_messages.parquet` exist and contain rows, and `code/data_acquisition.py` implements the required logic with tenacity back‑off. However, the required `pull_request.schema.yaml` file is missing, so the parquet files cannot be verified to conform to the specified schema, violating the task’s verification criteria. Adding the missing schema file (and optionally ensuring the optional fields are populated) is needed to complete the task.
- **T003** — Checked `code/prompt_engineering.py` (present and implements the logic) and the required output `data/processed/intent_prompts.parquet` (missing). The unit test also fails due to a `NameError`, confirming the script has not successfully produced the required parquet file.
- **T004** — Requested task execution failed; rerun successfully: code/synthetic_generation.py exit=1
