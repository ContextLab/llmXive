# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The Parquet file and checksums exist and row counts (1000 per language) match, but the unit test `test_raw_chunks_content` FAILED with "Avg length: 0.0", showing the required `content` column is empty in the actual Parquet data — the raw code content was not persisted. The implementer must fix the download script so real file contents are written to the `content` column (not just repo_name/language metadata), then regenerate the Parquet and checksums.
- **T003** — Requested task execution failed; rerun successfully: code/data/static_analysis.py exit=1; code/data/static_analysis_execute.sh exit=1
