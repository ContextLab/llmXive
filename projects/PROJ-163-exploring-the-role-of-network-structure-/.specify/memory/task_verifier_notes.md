# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directory structure (`code/`, `data/raw/`, `data/processed/`, `tests/`) is provided; the implementer did not supply any artifact showing these folders exist or contain files.
- **T002** — No project initialization artifacts (e.g., a repository, `pyproject.toml`, `requirements.txt`, or any code showing a Python 3.11 environment with the listed dependencies) were provided. Consequently, the claim that the Python project with the required packages has been set up cannot be verified.
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) were presented, so the required artifacts for configuring ruff/flake8 and Black are missing.
- **T006** — No artifact (e.g., a Python module, configuration file, or script) was provided that demonstrates loading IBM Quantum API tokens or setting default configuration values. Without such code or a documented setup, the requirement to “setup environment configuration management (load IBM Quantum API tokens/defaults)” is not satisfied. The implementer must supply the actual configuration‑loading implementation.
- **T010** — The required test file `tests/test_fetcher.py` does not exist, and the referenced schema file `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/raw_calibration.schema.yaml` (or `schema.yaml`) is also missing, so no contract test or validation code is present. The task’s core artifact is absent.
- **T016** — No evidence of any files under `data/raw/` containing the raw JSON calibration snapshots, nor any accompanying timestamps or checksum metadata, is provided. The required artifact is missing, so the task is not satisfied.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/raw_calibration.csv
- **T024** — No code, tests, or documentation were provided showing that disconnected graphs are detected, that the spectral gap is set to 0 for such graphs, or that path‑length metrics are computed only on connected components. Without these artifacts, the requirement cannot be verified.
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/graph_metrics.csv
- **T034** — declared artifact(s) missing/empty/invalid: data/processed/correlation_results.csv
- **T037** — declared artifact(s) missing/empty/invalid: docs/report.md
