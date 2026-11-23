# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The Parquet file and checksums.txt exist and the log shows a real streaming run from `codeparrot/github-code` writing 2000 rows, but there is no evidence of the required per-language breakdown: the log never reports counts per language (Python vs. Java), the visible Parquet content shows only repo names with no confirmed `language` column values, and the value of N (from Phase-0 power analysis) is never stated or verified. The task's core verification — "contains exactly N rows per language" — is unproven; the implementer should log/verify per-language row counts (e.g., a groupby on `language`
- **T003** — Requested task execution failed; rerun successfully: code/data/static_analysis.py exit=1; code/data/static_analysis_execute.sh exit=1
