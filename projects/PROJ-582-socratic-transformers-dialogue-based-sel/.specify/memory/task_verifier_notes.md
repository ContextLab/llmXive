# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The response contains only the task description and no actual `ls -R` output or any other proof that the specified directories were created; therefore we cannot verify that the required directory tree exists. The implementer must provide concrete evidence (e.g., a recursive directory listing) showing all listed folders are present.
- **T001b** — The evidence shows that `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt` does not exist, even though the task explicitly requires this file (and its sibling `src/__init__.py` and `tests/__init__.py`) at that path. The missing `requirements.txt` means the verification step fails. The implementer must create the required file (and ensure the other two files are also present at the specified location).
- **T003** — declared artifact(s) missing/empty/invalid: pyproject.toml, ruff.toml
- **T010** — declared artifact(s) missing/empty/invalid: src/data/verify_datasets.py
- **T004** — No evidence was presented showing that the `data/raw/`, `data/processed/`, and `data/results/` directories (or the required `.gitkeep` placeholder files) actually exist in the repository. Without these artifacts, the task requirement is not satisfied. The implementer must add the three directories and place a `.gitkeep` file in each (or otherwise demonstrate their presence).
- **T005** — declared artifact(s) missing/empty/invalid: src/utils/logging.py
- **T006** — declared artifact(s) missing/empty/invalid: src/utils/config.py
