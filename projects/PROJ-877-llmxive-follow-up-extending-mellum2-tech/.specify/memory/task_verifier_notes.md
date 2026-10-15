# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The Parquet file is only 25,661 bytes for a claimed 1,000 rows — roughly 25 bytes per row — which is impossible if the `content` column holds actual source-code chunks from `codeparrot/github-code`; the hex dump shows repo names but no code content, strongly suggesting the content field is empty or a stub. Additionally, the required verification (unit test `tests/unit/test_download.py`) TIMED OUT after 600s with exit code -1, so the row-count-per-language check never passed, and there is no evidence the required columns (`id`, `repo_name`, `language`, `content`, `status`) are all present and p
- **T003** — Requested task execution failed; rerun successfully: code/data/static_analysis.py exit=1; code/data/static_analysis_execute.sh exit=1
