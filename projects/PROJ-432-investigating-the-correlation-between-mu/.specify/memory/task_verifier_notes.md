# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory structure or file listing is provided; the implementer did not supply evidence that the required folders (`src/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/`, `logs/`, `config/`) exist. The task remains undone.
- **T001b** — No evidence of a Git repository being initialized nor a `.gitignore` file for Python/project data artifacts is provided; the required artifacts are missing.
- **T002a** — No Python 3.11 virtual‑environment creation or activation script is present in the provided evidence; the only content shown is a feature specification unrelated to the requested task. The required artifact is missing, so the task is not satisfied.
- **T003** — No linting/formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black.toml`, or a `pre-commit` hook) are present, nor any documentation showing that ruff and black have been set up for the project. The required artifacts to prove the task’s completion are missing.
- **T007** — No evidence of the required `tests/unit/` and `tests/integration/` directories (or any files within them) was provided; without these artifacts the task of setting up the test directory structure is not satisfied.
- **T008** — declared artifact(s) missing/empty/invalid: conftest.py
- **T009** — The repository contains a non‑empty `src/data/ingest.py`, but the required output file `data/raw/icecube.csv` is absent, and the script uses placeholder URLs without guaranteeing a real download. The caching artifact the task mandates does not exist.
- **T010** — The required output file `data/raw/era5.csv` is absent, and the provided `src/data/ingest.py` contains only placeholder/comments for ERA5 fetching without a concrete implementation that writes the data to that path. The task’s core requirement—to fetch ERA5 pressure‑level data (1000 hPa–10 hPa) and cache it as `data/raw/era5.csv`—is therefore not satisfied.
- **T013** — No `logs/alignment.json` file or its contents were supplied, so we cannot confirm that exclusion events are being logged in the required JSON list format or that all events are captured. The implementer must provide the actual log file with correctly structured entries.
