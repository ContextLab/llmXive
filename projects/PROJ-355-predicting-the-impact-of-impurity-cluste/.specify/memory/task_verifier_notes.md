# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory tree or file list was provided showing the creation of `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/` with the required subfolders, nor any script or log confirming idempotent execution. The required artifact (the initialized project structure) is missing.
- **T001b** — No `.gitignore` file was found in the specified directory (`projects/PROJ-355-predicting-the-impact-of-impurity-cluste/`), and no content was provided to verify that it contains the required exclusions (`data/`, `results/`, `*.pyc`, `__pycache__`). The task therefore lacks the mandatory artifact.
- **T001c** — No README.md file or its contents were provided for `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/`; the claim lacks any artifact to verify. The required documentation with project title, execution instructions, and data provenance details is missing.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` entries, `ruff.toml`, `black` config, or CI scripts) were presented for the `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/` directory, so there is no evidence that ruff and black have been set up. The required artifacts are missing.
- **T004a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T004b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No evidence of the required `data/raw/`, `data/processed/`, or `results/` directories (each containing a `.gitkeep` file) was provided; the artifact is missing.
- **T009** — No `tests/unit/` or `tests/integration/` directories or any scaffold files (e.g., `__init__.py`, sample test modules) are present in the provided evidence, so the required scaffolding has not been delivered.
- **T027** — The repository lacks the required `contracts/dataset.schema.yaml` file, and while `train.py` defines `load_schema` and `validate_input_data`, the shown code never loads the schema or calls the validation function before model training. Consequently, the contract validation step is not actually performed.
