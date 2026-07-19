# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No `specs/001-comparative-analysis-of-molecular-fingerprints/data-model.md` file or its contents were presented; therefore the required schema definitions for Compound, Fingerprint, Model, and PerformanceMetric are missing. The implementer must supply this markdown file with the appropriate entity specifications.
- **T001** — No directory listing or other proof was provided showing that `projects/PROJ-678-comparative-analysis-of-molecular-fingerprints/` and its subdirectories (`data/raw/`, `data/processed/`, `code/`, `tests/`) actually exist; without such evidence the required artifact is missing.
- **T004** — No evidence of the required `data/raw/` and `data/processed/` directories (or their `.gitkeep` placeholder files) was provided; without confirming these paths exist and contain the placeholder files, the task requirement is not satisfied.
- **T007** — No evidence was provided showing a `tests/` directory with the required `unit/` and `integration/` subfolders; the claim lacks any artifact confirming the directory structure exists.
- **T012** — The required output file `data/processed/organophosphates_filtered.csv` does not exist, and the provided `code/filter.py` is incomplete (truncated, no main routine that actually loads data, applies the exact SMARTS `[P](=O)([O,SC])[O,SC]`, and writes to the specified path). The implementation therefore does not fulfill the task.
- **T013** — The provided `code/filter.py` does not contain logic to check for endpoint sample sizes < 50, issue a “Low Sample Size” warning, or skip statistical tests, nor does it write any such limitation to `data/processed/filter_log.txt` (the log file is missing). Consequently the task’s validation and logging requirements are not satisfied.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/filter_log.txt
- **T029** — declared artifact(s) missing/empty/invalid: data/processed/research_results.md
- **T030** — declared artifact(s) missing/empty/invalid: data/processed/research_results.md
