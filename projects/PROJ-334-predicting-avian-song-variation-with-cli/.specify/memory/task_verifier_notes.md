# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The repository contains the required `.ruff.toml`, `pyproject.toml` with a `[tool.black]` section, and a `.pre-commit-config.yaml`, but there is no evidence that the verification steps (`ruff check .` and `black --check .`) were actually run and returned exit 0. Execution logs or CI results are needed to confirm the tools are correctly configured.
- **T001** — Checked `data/raw/analysis_dataset.parquet` (present with correct SHA‑256) and `data/checksums.txt` (line with matching hash). However the required project state YAML file was not created – the test `test_state_updated` failed because `/projects/state/.../PROJ-334-predicting-avian-song-variation-with-cli.yaml` is missing, so `utils.update_state_file()` did not record the checksum as required.
- **T018** — Requested task execution failed; rerun successfully: code/ingestion.py exit=1
