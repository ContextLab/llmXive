# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`code/`, `data/`, `results/`, `tests/`) is provided; the implementer did not supply a directory listing or any files showing that the project structure has been created.
- **T002** — The provided material contains only a feature specification and user stories; there is no evidence of a Python 3.11 project being created (e.g., no `pyproject.toml`, `requirements.txt`, `setup.cfg`, or similar file) and none of the listed dependencies are declared or installed. Consequently, the task of initializing the project with the required packages has not been demonstrated.
- **T003** — The implementer supplied only a feature specification for gene‑essentiality analysis and no linting/formatting configuration files, scripts, or documentation (e.g., `pyproject.toml`, `.ruff.toml`, Black config, or pre‑commit hooks). Consequently, the required artifacts for configuring ruff and black are missing.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — declared artifact(s) missing/empty/invalid: data/phylogeny/tree.newick
- **T017** — The `code/main.py` file stops before writing any output (the snippet ends after defining `output_file` and no `json.dump` or similar is present), and the expected `results/correlations.json` file does not exist on disk. Consequently the orchestration loop does not complete the download‑map‑centrality‑correlation‑save sequence required by the task.
- **T020** — No code, tests, or documentation were provided showing that the pipeline now assigns a centrality of 0 for disconnected network components or that it logs a warning and skips organisms with no gene overlap. Without such artifacts, we cannot confirm the required error‑handling behavior was implemented.
