# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked `code/requirements.txt` (contains all required pinned packages) and `specs/001-code-maintainability-impact/quickstart.md` (documents runnable command). However the repository lacks a `.env.example` file defining `GITHUB_TOKEN`, `DATA_PATH`, and `LOG_PATH`, and no logging configuration file is present, both of which are required by the task.
- **T002** — The script `code/01_data_curation.py` runs and logs successful cloning, but the required output files `data/raw/repo_list.csv` and `data/raw/repo_metadata.csv` are absent from the repository (both marked MISSING). The task explicitly demands these CSVs be saved in `data/raw/`; without them the curation output is not produced. The next implementer must ensure the script writes the CSVs to the correct `data/raw/` directory and verify the files exist after execution.
- **T003** — Requested task execution failed; rerun successfully: code/03_code_block_extraction.py exit=1
