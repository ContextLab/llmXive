# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`code/`, `tests/`, `data/`, `models/`, `reports/`) is provided; the artifact list is empty, so the project structure has not been demonstrated.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black/Ruff settings, `.flake8` config, or a `requirements-dev.txt` including these tools) or setup scripts are present in the provided evidence. Consequently, the task of configuring ruff/flake8 and Black has not been demonstrated.
- **T007** — No `data/` directory with the required subfolders (`raw/`, `curated/`, `artifacts/`) is present, nor any script or code implementing checksum generation/verification for files in those folders. The implementer provided only narrative text without the actual filesystem changes or checksum logic, so the task is not satisfied.
- **T008** — The required output file `data/raw/fetched_diffusion.csv` is missing, and the provided `acquisition.py` contains placeholder logic and comments about “simulating” diffusion values rather than actually fetching and writing real data as specified. The script does not demonstrably save a CSV or log the exact warning message when N < 50.
