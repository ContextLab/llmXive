# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `data/raw/` directory contains only a `.gitkeep`; the required `<owner>_<repo>.parquet` files and `commit_messages.parquet` are missing, and the `pull_request.schema.yaml` file is absent, so the task’s output artifacts do not exist.
- **T003** — The required output file `data/processed/intent_prompts.parquet` does not exist (and the raw input `data/raw/commit_messages.parquet` is also missing), and the provided test fails because it cannot monkey‑patch the toolkit’s path root, so the script’s behavior is not demonstrated. The task’s core artifact is absent.
- **T004** — Requested task execution failed; rerun successfully: code/synthetic_generation.py exit=1
