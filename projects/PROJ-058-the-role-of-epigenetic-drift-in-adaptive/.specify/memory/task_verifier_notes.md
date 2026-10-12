# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001c** — The evidence shows `output/`, `output/figures/`, `tests/`, `tests/unit/`, `tests/contract/`, and `data/processed/` directories exist, but the required `logs/` directory is not present in the listed artifacts. The task therefore is not fully satisfied.
- **T002** — The evidence only shows the project root path; there is no pyproject.toml, requirements.txt, environment.yml, or any other manifest that lists Python 3.11 and the required packages (pandas, numpy, scipy, scikit‑learn, requests, pyyaml, tqdm, pytest). Without such a file the claim of an initialized Python 3.11 project with those dependencies is unsupported.
- **T003** — No configuration files or scripts for ruff linting or black formatting are present in the provided artifact list (e.g., no `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`, or similar files), so the task of configuring these tools is not demonstrated. The implementer has not supplied any evidence that the tools are installed, configured, or integrated into the project.
- **T005** — The evidence includes a non‑empty `code/__init__.py`, but no second `__init__.py` file for the requested module/package (e.g., a top‑level or sub‑package `__init__.py`). The task explicitly required both files, so the missing module `__init__.py` must be added.
- **T011** — Requested task execution failed; rerun successfully: code/discovery/query_geno.py exit=1
- **T012** — Requested task execution failed; rerun successfully: code/discovery/query_geno.py exit=1
