# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`code/`, `data/`, `tests/`, `docs/`) is presented; the response contains only the task description and no actual file‑system artifacts, so the project structure has not been demonstrated.
- **T003** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T006** — No evidence of a `code/data/` directory (with `raw/` and `processed/` subfolders) is provided; the response contains only the task description and no filesystem artifacts. The required directory structure is missing.
- **T007** — The required schema files (e.g., `docs/contracts/dataset.schema.yaml`, `docs/contracts/input.schema.yaml`) are missing; the only mentioned file `schema.yaml` does not exist, so no data schemas have been defined as required.
- **T010** — declared artifact(s) missing/empty/invalid: code/data/loader.py
- **T014** — declared artifact(s) missing/empty/invalid: code/models/predictor.py
- **T016** — No `main.py` file or code changes were presented, and there is no evidence that validation logic checking for at least 50 samples per alloy family was added. The required artifact (updated `main.py` containing the abort‑on‑insufficient‑samples check) is missing.
- **T017** — No code, script, or generated `predictions.csv` / `new_predictions.csv` files were provided; the evidence contains only the specification text, so there is no artifact demonstrating that the required saving logic has been implemented. The implementer must supply the actual implementation (e.g., a Python module or pipeline step) and the resulting CSV files to satisfy the task.
- **T018** — No code, configuration, or `pipeline.log` file was provided to demonstrate that the pipeline now records all warnings and hyper‑parameters as required by FR‑007. The implementer’s claim cannot be verified without an actual artifact showing the logging implementation.
