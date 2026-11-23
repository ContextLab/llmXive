# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `configs/` directory is missing, and there is no `logs/` directory present, so the required layout is not fully created. The existing `code/`, `tests/`, `data/`, and `docs/` directories (with `__init__.py` files) are correct, but the missing directories cause the task to be incomplete.
- **T002** — The provided `requirements.txt` includes all required packages (plus an extra one), but there is no evidence of a `setup_env.sh` script, nor any indication that such a script creates a virtual environment without errors. The missing setup script must be added and verified.
- **T003** — No pre‑commit configuration file, ruff/black setup, or output from `pre-commit run --all-files` is present; the required artifacts to demonstrate that linting and formatting are correctly configured and pass are missing.
- **T004** — The repository contains the required `code/logging/pipeline_logger.py` implementation, but no evidence that a dummy script was run, that a log file was created, or that the file contains a correctly‑formatted JSON line as the verification step demands. The implementer must add the execution output (e.g., a script, the generated `logs/run_*.log` file, and a sample JSON entry).
- **T005** — The `config_loader.py` file exists and implements a YAML loader, but the required `configs/` directory (containing a sample YAML file) is missing, so the verification step of loading a sample file and asserting expected keys cannot be performed. Add a `configs/` folder with a YAML file and a test that loads it and checks its keys.
- **T008** — The two schema files exist and contain syntactically valid JSON‑Schema draft‑07 definitions, but the task required that the schemas be validated with the `jsonschema` CLI. No command output, test run, or proof of successful validation is provided, so the verification step is missing.
- **T032** — declared artifact(s) missing/empty/invalid: output/provenance.yaml
- **T064** — declared artifact(s) missing/empty/invalid: data/processed/validation_subset.csv
- **T039** — declared artifact(s) missing/empty/invalid: validation/validation_report.yaml
