# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — No `state_manager.py` file or any code was presented, and there is no evidence that a YAML state file was updated with SHA‑256 hashes for a test file. The required artifact is missing, so the task is not satisfied.
- **T012a** — The repository lacks the required `data/raw/nrel_perovskites.csv` file, and `code/data_ingestion.py` does not implement a `fetch_and_validate_data` function nor contain logic that writes the CSV with a non‑null `T_d` column. Consequently the task’s core output is missing.
- **T012b** — The repository lacks a `fetch_and_validate_data` function in `code/data_ingestion.py` and does not contain the required `data/raw/mp_perovskites.csv` file; consequently the task’s core behavior (fetching from the Materials Project API, validation, filtering for `T_d`, and writing the CSV) is not present. The missing CSV also means the verification condition (existence and non‑null `T_d` column) cannot be satisfied.
