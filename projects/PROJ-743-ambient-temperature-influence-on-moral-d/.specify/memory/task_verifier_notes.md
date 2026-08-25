# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — The required output file `data/raw/era_sample.h5` is missing, and the log does not show any actual validation of hourly resolution or temperature values. The script exists, but there is no evidence it was run successfully to produce the required sample and verification logs.
- **T002c** — The required output file `data/raw/era5_full.h5` does not exist, and the log does not contain any entry confirming that `fetch_era_full.py` successfully fetched, merged, and saved the dataset. Without the H5 file (and a proper success/failure log entry), the task’s core requirement is unmet.
- **T002d** — declared artifact(s) missing/empty/invalid: data/raw/era5_full.h5, state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml
- **T003** — declared artifact(s) missing/empty/invalid: data/raw/era5_sample.h5, state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml
- **T007** — No directory listing or other evidence was provided showing that the required folders (`code/`, `data/raw/`, `data/processed/`, `results/figures/`, `results/logs/`, `results/stats/`, `tests/`) actually exist; thus the task’s deliverable cannot be confirmed. The implementer must supply a file‑system snapshot or command output proving the structure is created.
- **T009** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) or scripts are present in the provided artifacts; the only evidence is a unrelated feature specification, which does not demonstrate that ruff/flake8 and black have been set up.
