# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — No `state/contradictions/FR-006-runtime-bug.md` file is present, nor any evidence that a time‑limit enforcement was added to subsequent tasks. The required documentation and enforcement are missing.
- **T001** — No directory tree or listing was provided to confirm that the required folders (`src/ingestion`, `src/modeling`, `src/visualization`, `src/utils`, `tests/contract`, `tests/integration`, `tests/unit`, `data/raw`, `data/processed`, `docs`) were actually created. The implementer must supply evidence (e.g., a printed `tree` or `ls -R` output) showing these paths exist.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, a pre‑commit hook file, or any script invoking Ruff/Black) were presented. Without these artifacts, the claim that linting and formatting tools are configured cannot be verified. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly set up.
- **T004** — declared artifact(s) missing/empty/invalid: src/utils/constants.py
- **T005** — declared artifact(s) missing/empty/invalid: src/utils/logging.py
- **T006** — declared artifact(s) missing/empty/invalid: src/utils/data_provenance.py, tests/unit/test_provenance.py
- **T007** — declared artifact(s) missing/empty/invalid: tests/unit/test_constants.py, tests/unit/test_logging.py
- **T008** — declared artifact(s) missing/empty/invalid: src/utils/config.py
- **T010** — The required file `tests/unit/test_preprocessing.py` does not exist, so no unit test for the weight% to atomic% conversion edge cases is present. The task’s deliverable is missing entirely.
- **T012** — declared artifact(s) missing/empty/invalid: src/ingestion/download_materials_project.py
- **T013** — The required `src/ingestion/download_supercon.py` file does not exist, and the provided `tests/unit/test_ingestion.py` only contains data‑filtering tests unrelated to downloading the SuperCon dataset or checking for a failure when >50 % of entries lack impurity columns. No unit test verifies that the script exits with code 1 under the specified condition.
- **T014** — declared artifact(s) missing/empty/invalid: src/ingestion/preprocess.py
- **T018** — declared artifact(s) missing/empty/invalid: src/modeling/train.py
- **T019** — declared artifact(s) missing/empty/invalid: src/modeling/train.py
