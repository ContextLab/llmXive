# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T048** — The repository contains a `loader.py` with checksum utilities, but it never invokes verification for `data/processed/subtle_cue_subset.parquet`, does not write results to `data/processed/integrity_log.txt`, and the required parquet file and log file are absent. Consequently the task’s three mandatory requirements are not satisfied.
