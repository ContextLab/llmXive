# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was provided showing that the specified directories (`src/brainnet`, `tests/unit`, `tests/contract`, `data/processed`, `data/raw`, `results/figures`, `metadata`, `contracts`) actually exist in the project. Without a directory listing, screenshots, or other proof, we cannot confirm the required project structure was created. The implementer must supply concrete proof (e.g., a tree listing or file system snapshot) that these folders are present.
- **T002** — No project files (e.g., `pyproject.toml`, `requirements.txt`, `setup.cfg`, or a virtual environment) were provided, and there is no evidence that a Python 3.11 project was created or that the listed dependencies were installed. The required artifact is missing.
- **T003** — No linting or formatting configuration files (e.g., pyproject.toml, .flake8, .ruff.toml, .isort.cfg) or setup scripts are present in the provided evidence, so the task of configuring ruff/flake8, black, and isort has not been demonstrated. The required artifacts are missing.
- **T005** — No `.gitignore` file or its contents were supplied; without the artifact we cannot confirm that data‑artifact and Python‑cache patterns are listed as required. The implementer must add a `.gitignore` containing entries such as `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`, `*.egg-info/`, `*.egg`, `*.ipynb_checkpoints/`, and any data directories (e.g., `data/`, `*.nii`, `*.csv`) to satisfy the task.
- **T006** — declared artifact(s) missing/empty/invalid: src/brainnet/utils.py
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — declared artifact(s) missing/empty/invalid: src/brainnet/preprocessing.py
