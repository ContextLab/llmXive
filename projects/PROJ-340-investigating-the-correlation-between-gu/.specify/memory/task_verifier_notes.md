# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T064** — The script `code/run_streaming_test.py` runs but never creates the required `data/processed/filtered_data.parquet` (the file is missing) and only simulates streaming rather than loading a dataset with a `streaming=True` flag. Consequently the core requirement of generating the parquet output via chunked accumulation is not met.
