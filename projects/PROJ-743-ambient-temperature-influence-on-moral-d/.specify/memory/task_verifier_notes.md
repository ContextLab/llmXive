# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — The required output file `data/raw/era_sample.h5` is missing, so the script was either not executed or failed to produce the hourly temperature sample. Without this HDF5 file the validation of hourly resolution and temperature values cannot be confirmed. The implementer must run `code/validate_era5.py` (ensuring CDS API access) so that `era_sample.h5` is created and the log reflects the actual validation results.
- **T002c** — The required output file `data/raw/era5_full.h5` does not exist, and the log does not contain any entry confirming that `fetch_era_full.py` successfully fetched, merged, and saved the dataset. Without the H5 file (and a proper success/failure log entry), the task’s core requirement is unmet.
- **T002d** — declared artifact(s) missing/empty/invalid: data/raw/era5_full.h5, state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml
- **T003** — declared artifact(s) missing/empty/invalid: data/raw/era5_sample.h5, state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml
- **T009** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, `black` settings) or related scripts are present in the provided evidence, so the requirement to configure ruff/flake8 and black cannot be verified as fulfilled.
