# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`src/`, `tests/`, `specs/001-predicting-reaction-mechanisms/`, `data/`, `state/projects/`) is provided; the claim lacks any artifact listing or screenshots confirming their existence. The implementer must supply a directory listing or similar proof that these folders have been created and are non‑empty.
- **T001b** — No `__init__.py` files were presented or listed for any of the subdirectories under `src/` or `tests/`; without concrete evidence of these files existing, the requirement cannot be considered satisfied. The implementer must add and show the `__init__.py` files in every subdirectory of both `src/` and `tests/`.
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or setup scripts are present in the provided evidence, so the requirement to configure ruff/flake8 and Black has not been demonstrated. The implementer must add the appropriate config files and ensure they are non‑empty and correctly set up.
- **T005** — declared artifact(s) missing/empty/invalid: src/utils/io.py
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — declared artifact(s) missing/empty/invalid: src/utils/seed.py
- **T033a** — declared artifact(s) missing/empty/invalid: src/analysis/dft_setup.py, data/reference/literature_db.json
- **T013** — No code changes or files were presented for `src/ingestion/load_*.py`; thus there is no evidence that provenance‑filtering logic was added or that any fallback mechanism was removed. The required artifact (the updated ingestion scripts) is missing.
- **T013b** — declared artifact(s) missing/empty/invalid: src/ingestion/merge_spectra.py, data/processed/fingerprints.parquet
- **T015** — declared artifact(s) missing/empty/invalid: src/ingestion/merge_spectra.py
- **T016** — declared artifact(s) missing/empty/invalid: src/ingestion/merge_spectra.py, data/results/class_balance_report.json
- **T017** — The required `data/checksums.json` file does not exist, and the `state/projects/PROJ-088-predicting-reaction-mechanisms-from-spec.yaml` file is also missing, so no checksums were recorded nor was the `artifact_hashes` map updated. The task therefore has not been fulfilled.
