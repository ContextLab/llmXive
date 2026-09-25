# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listing or file‑system snapshot was provided showing that the `projects/PROJ-407-predicting-herbivore-resistance-fr/` folder contains the required sub‑directories (`code`, `data/raw`, `data/interim`, `data/processed`, `data/results`, `tests/unit`, `tests/integration`, `tests/contract`). Without concrete evidence of these folders existing, the task requirement is not satisfied. The implementer must supply a view of the project tree (e.g., output of `tree` or `ls -R`) confirming the structure.
- **T003** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T005** — The `code/versioning.py` file is truncated (the `main` function ends abruptly with `update_state_file(pr` and lacks the rest of its logic, making it non‑functional. Additionally, the required state file `state/projects/PROJ-407-predicting-plant-herbivore-resistance-fr.yaml` does not exist. Both the implementation and the artifact update are missing, so the task is not completed.
- **T006** — No evidence of the required directory structure (`code/`, `data/raw/`, `data/interim/`, `data/processed/`, `tests/`) is presented; the implementer did not provide any listing, screenshots, or file‑system output showing these folders exist. The task remains unfinished until the directories are created and verified.
- **T009** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The provided `code/ingest.py` does not contain any code that defines the Low/Med/High → 1/2/3 mapping or writes such a dictionary to `data/interim/ordinal_mapping.log`. Moreover, the `ordinal_mapping.log` file is absent from the repository. Both the conversion implementation and the required log artifact are missing.
- **T014** — declared artifact(s) missing/empty/invalid: data/raw/raw_dataset.csv, data/raw/raw_dataset.csv.sha256
- **T015** — declared artifact(s) missing/empty/invalid: data/interim/harmonized.csv
- **T022** — declared artifact(s) missing/empty/invalid: code/model.py
- **T023** — declared artifact(s) missing/empty/invalid: code/model.py
- **T024** — declared artifact(s) missing/empty/invalid: code/model.py
- **T028** — declared artifact(s) missing/empty/invalid: tests/unit/test_model.py
- **T029a** — The repository lacks the required output files (`null_distribution.csv`, `permutation_p_value.json`, `permutation_run.log`) and the `run_permutation_test` function is truncated/incomplete, with no evidence that it performs stratified shuffling or writes the specified artifacts. The task’s core deliverables are therefore not present.
- **T029b** — declared artifact(s) missing/empty/invalid: data/interim/batch_corrected_data.csv
