# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of a `code/` directory or an `__init__.py` file was provided; the prompt contains no artifact listing or file contents to verify that the required structure exists. The implementer must add the `code/` folder with an `__init__.py` (and any other expected sub‑directories) to satisfy the task.
- **T001b** — No evidence of a `data/` folder with the required sub‑directories (`raw/`, `processed/`, `results/`) or a `data/.gitkeep` file is present; the implementer did not provide any artifact confirming the directory structure was created.
- **T011** — The required file `tests/unit/test_extraction.py` does not exist in the repository, so no unit test verifying parsing of inequalities and effect sizes is present. The task’s core artifact is missing.
- **T012** — The required artifact `tests/integration/test_pipeline_us1.py` does not exist, so no integration test is present to verify the 10‑pair subset pipeline behavior. The task cannot be considered fulfilled until this file is added with the appropriate test logic.
- **T014** — The provided `code/01_fetch_and_match.py` ends abruptly (truncated at `def is_theoretic`) and contains no implementation of the required filtering logic or CSV‑column `exclusion_reason` handling, nor does it write to `data/raw/exclusion_log.csv` (the file is absent). Consequently the task’s filtering and logging requirements are not met.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/matched_pairs.csv
