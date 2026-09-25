# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listing or file‑system snapshot was provided showing that the `projects/PROJ-407-predicting-herbivore-resistance-fr/` folder contains the required sub‑directories (`code`, `data/raw`, `data/interim`, `data/processed`, `data/results`, `tests/unit`, `tests/integration`, `tests/contract`). Without concrete evidence of these folders existing, the task requirement is not satisfied. The implementer must supply a view of the project tree (e.g., output of `tree` or `ls -R`) confirming the structure.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- `T005` (rejected 1x): The `code/versioning.py` file is truncated (the `main` function ends abruptly with `update_state_file(pr` and lacks the rest of its logic, making it non‑functional. Additionally, the required state file `state/projects/PROJ-407-predicting-plant-herbivore-resistance-fr.yaml` does not exist. Both the implementation and the artifact update are missing, so the task is not completed.
- `T006` (rejected 1x): No evidence of the required directory structure (`code/`, `data/raw/`, `data/interim/`, `data/processed/`, `tests/`) is presented; the implementer did not provide any listing, screenshots, or file‑system output showing these folders exist. The task remains unfinished until the directories are created and verified.
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T012` (rejected 1x): The provided `code/ingest.py` does not contain any code that defines the Low/Med/High → 1/2/3 mapping or writes such a dictionary to `data/interim/ordinal_mapping.log`. Moreover, the `ordinal_mapping.log` file is absent from the repository. Both the conversion implementation and the required log artifact are missing.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/raw_dataset.csv, data/raw/raw_dataset.csv.sha256
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/interim/harmonized.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

