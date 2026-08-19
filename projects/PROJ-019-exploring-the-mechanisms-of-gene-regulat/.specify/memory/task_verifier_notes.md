# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — The `code/main.py` defines `run_ingestion` and writes a JSON file, but the required output file `data/processed/ingestion_summary.json` is missing, and the `cell_types` list is sorted rather than preserving the exact order `['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']`. The implementation therefore does not fully meet the task specifications.
- **T032** — The provided `code/main.py` does not contain a `run_validation_report` function, nor does it create `data/processed/validation_report.json`. The required JSON file is absent from the repository. Consequently, the task’s specification is not satisfied.
- **T033** — declared artifact(s) missing/empty/invalid: data/processed/enrichment_matrix.csv, data/processed/validation_report.json, data/processed/summary_table.csv
- **T034** — No actual `README.md` or `specs/001-gene-regulation/quickstart.md` content was provided; without seeing the updated files we cannot confirm that the required documentation changes were made. The implementer must supply the modified files (or their contents) showing the documentation updates.
- **T037** — No evidence of any files under `tests/unit/` was provided; without actual unit test files present, the requirement for “Additional unit tests in `tests/unit/`” is not satisfied. The implementer must add non‑empty test modules in that directory.
- **T038** — No evidence of a `quickstart.md` validation run, CI logs, or reproducibility report is provided; the implementer supplied only the task description without any artifacts demonstrating that the validation was executed successfully.
