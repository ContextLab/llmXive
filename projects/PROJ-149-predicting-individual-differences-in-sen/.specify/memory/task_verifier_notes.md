# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The evidence shows `code/`, `tests/`, `data/interim/`, `data/processed/`, and `code/utils/` directories exist, but the required `data/raw/` directory is missing. The task’s core requirement—to create the full project directory structure including `data/raw/`—is therefore not satisfied.
- **T001b** — The `code/requirements.txt` file is present, but it does not contain **pinned** version specifications (it uses `>=` ranges) and includes many extra packages beyond the nine listed in the task. The requirement to list exact version numbers for the specified libraries is therefore not satisfied.
- **T003** — The evidence contains no linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) and no documentation showing that flake8/black have been set up and run. These required artifacts are missing, so the task is not satisfied.
- **T004a** — The provided `code/config.py` defines the required constants (EPSILON, OVERLAP = 0.5, WINDOW_SIZE = 4), band definitions, ICA parameters, and path helpers, but it contains no code to accept `--overlap` (or `--window-size`) command‑line arguments and adjust the configuration at runtime. Without a CLI parsing mechanism or documented override interface, the file does not meet the mandatory “support `--overlap` override” (and optional `--window-size` override) requirement. Adding argparse handling (or equivalent) that updates the OVERLAP and WINDOW_SIZE values based on supplied flags is needed.
- **T012b** — declared artifact(s) missing/empty/invalid: code/04b_aggregate_bands.py, data/interim/psd_spectra.npy, data/interim/band_powers.csv
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json
- **T025a-config** — declared artifact(s) missing/empty/invalid: data/interim/robustness_window_params.json
- **T025a-verify** — declared artifact(s) missing/empty/invalid: data/interim/robustness_window_eeg/, data/interim/robustness_window_exclusion_log.csv
- **T025f-config** — declared artifact(s) missing/empty/invalid: data/interim/robustness_ica_params.json
- **T031b** — declared artifact(s) missing/empty/invalid: code/11b_format_tables.py
- **T008-report-gate** — declared artifact(s) missing/empty/invalid: data/processed/feasibility_report.md, data/interim/halt_signal.json
- **T041** — declared artifact(s) missing/empty/invalid: code/09_robustness_preprocess_window.py, code/09_robustness_preprocess_ica.py
