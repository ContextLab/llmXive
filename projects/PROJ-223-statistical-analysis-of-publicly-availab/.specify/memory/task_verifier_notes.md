# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No `code/` directory or the required Python files (`__init__.py`, `config.py`, `ingest.py`, `model.py`, `diagnostics.py`, `utils.py`, `main.py`) are present in the provided artifacts; therefore the task’s core deliverable is missing. The implementer must add the directory and populate each file with appropriate, non‑placeholder code.
- **T001b** — No evidence of a `tests/` directory or the required files (`__init__.py`, `test_ingest.py`, `test_model.py`, `test_diagnostics.py`) was provided; without these artifacts the task requirement is not satisfied.
- **T016** — The `code/ingest.py` defines a `validate_merged_output` function, but the implementation is truncated (no return statement) and the required `merged_dataset.schema.yaml` file is missing from the repository, so the validation step cannot actually be performed. The missing schema file and incomplete function must be added/fixed for the task to be satisfied.
