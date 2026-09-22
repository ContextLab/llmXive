# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004a** — The unit tests expect `data/processed/cutoff_depth_validation.json` to be created by `validate_cutoff_depth`, but the file is missing, indicating the function either does not write the file or the write step is incomplete. The missing output file must be generated (and contain the returned JSON) for the task to be considered complete.
- **T061** — No README.md, quickstart.md, or research.md files (or any diff/report) are provided, nor any evidence that they were compared against the code and outputs. The implementer did not supply the required documentation review artifacts.
- **T062** — No evidence (e.g., command output, log files, or a report) showing that `ruff check code/` and `black --check code/` were run and returned zero errors is present, so we cannot confirm the codebase is properly formatted and lint‑free. The implementer must provide the verification output or a summary confirming no formatting/linting issues.
