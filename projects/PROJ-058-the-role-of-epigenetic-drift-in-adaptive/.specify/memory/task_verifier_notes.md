# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The evidence shows that the `data/` directory exists, but the required `data/raw/` subdirectory is missing. The task explicitly demands creation of both directories, so the implementation is not complete.
- **T001c** — The evidence shows that `tests/`, `tests/unit/`, and `tests/contract/` directories exist, but the required `data/processed/`, `output/`, `output/figures/`, and `logs/` directories are missing. These absent directories must be created to satisfy the task.
- **T002** — The evidence only shows the project root path; there is no pyproject.toml, requirements.txt, environment.yml, or any other manifest that lists Python 3.11 and the required packages (pandas, numpy, scipy, scikit‑learn, requests, pyyaml, tqdm, pytest). Without such a file the claim of an initialized Python 3.11 project with those dependencies is unsupported.
- **T003** — No configuration files or scripts for ruff linting or black formatting are present in the provided artifact list (e.g., no `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`, or similar files), so the task of configuring these tools is not demonstrated. The implementer has not supplied any evidence that the tools are installed, configured, or integrated into the project.
- **T011** — Requested task execution failed; rerun successfully: code/discovery/query_geno.py exit=1
