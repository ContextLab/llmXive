# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — The repository contains a large `code/ingestion.py` but the visible portion ends before any dataset‑fetching logic, and no `try/except` around a fetch call is shown. Moreover, the required `data/logs/fetch_error.log` file does not exist, so the script cannot be writing the detailed error log as specified. The task’s error‑handling requirement is therefore not met.
- **T010a** — No `test_features.py` file or `test_mixing_enthalpy` unit test is present in the provided artifacts, so the required unit test does not exist or is empty. The implementer has not supplied the test code that should run after T014.
- **T010b** — No `test_features.py` file or the specific `test_size_mismatch` unit test is present; the only evidence is a high‑level feature specification, not the required test code or its execution results. The task demands a concrete unit test artifact, which is missing.
- **T016a** — declared artifact(s) missing/empty/invalid: data/processed/processed_alloys.csv
- **T020** — No code, notebook, script, or output file showing that `processed_alloys.csv` was loaded and split with `random_state=42` and `test_size=0.2` is present. The required artifact (e.g., a Python script, Jupyter notebook, or saved train/test CSVs) is missing, so the task is not satisfied.
