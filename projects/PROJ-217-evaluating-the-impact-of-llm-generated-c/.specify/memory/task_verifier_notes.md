# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The script, JSONL outputs, excluded records, checksum manifest, and tests all exist and look genuine (500 raw records, 498 valid, 2 excluded with reasons, SHA-256 recorded). However, the required log file `data/dataset_preparation.log` is MISSING — the script writes it only at the end of `main()`, so its absence also suggests the run may not have completed successfully (exit 0 unverified). The implementer must run the script to completion so the log with total/valid/excluded counts and SC-006 compliance is actually produced.
- **T002** — Requested task execution failed; rerun successfully: src/data/generate_comments.py exit=1
