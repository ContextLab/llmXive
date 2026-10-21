# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The script, JSONL outputs, excluded records, checksum manifest, and tests all exist and look correct, but the required log file `data/dataset_preparation.log` is MISSING — the verification criteria explicitly require it to exist and report total/valid/excluded counts and SC-006 compliance. The implementer should re-run the script (or otherwise produce the log) so the summary log is written to `data/dataset_preparation.log`.
- **T002** — Requested task execution failed; rerun successfully: src/data/generate_comments.py exit=1
