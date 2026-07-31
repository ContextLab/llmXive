# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No artifact showing a `code/` directory or an `__init__.py` file was provided; the evidence list is empty, so the required files cannot be confirmed to exist. The implementer must add the `code/` folder with a non‑empty `__init__.py` inside.
- **T001b** — No evidence of a `tests/` directory or its required sub‑folders (`contract/`, `unit/`, `integration/`) was provided; the implementer’s claim cannot be verified from the supplied artifacts. The missing directory structure must be added and shown.
- **T001c** — No evidence of a `data/` directory or its required subfolders (`raw/`, `processed/`, `results/`, `config/`) was provided; the implementer’s claim is unsupported by any visible artifacts.
- **T002b** — No `.gitignore` file or virtual environment configuration (e.g., `requirements.txt`, `pyproject.toml`, or `venv/` setup script) was presented. Without these artifacts, the claim that the task “Create `.gitignore` and initialize virtualenv configuration” is fulfilled cannot be verified. The next implementer must add a proper `.gitignore` file and provide the necessary virtual environment setup files.
- **T004a** — The required `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` file is missing, and the runtime configuration file `data/config/research_design.yaml` that should contain the list of taxa does not exist. Without these artifacts the predictor schema is not defined and the required taxa list is not provided.
- **T004b** — The required files `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` and `data/config/research_design.yaml` are missing from the repository, so no schema or runtime metric list is present. Without these artifacts the task’s requirement is not satisfied.
- **T005a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: github/workflows/analysis.yml
- **T014c** — The required file `data/processed/filtered_data.parquet` does not exist, so no checksum can be computed. Moreover, the YAML file does not contain a checksum entry for that parquet file (only a code file entry is present). Both the artifact and its recorded checksum are missing.
- **T016** — The repository lacks the required `data/results/timing_evidence.json` file, and the shown portion of `code/main.py` does not contain any execution‑timing logic (recording start/end, asserting < 6 h, writing the JSON, or exiting on timeout). Both the artifact and the core functionality are missing.
- **T016b** — declared artifact(s) missing/empty/invalid: data/results/timing_evidence.json, data/results/final_report.md
- **T020a** — declared artifact(s) missing/empty/invalid: code/transform.py, data/metadata/compositionality_flag.json
