# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required `projects/PROJ-037-investigating-the-correlation-between-gu/` directory or its subfolders (`data/raw/`, `data/processed/`, `data/outputs/`, `code/`, `tests/`, `docs/`) is present. The implementer must create and show this directory tree.
- `T002b` (rejected 1x): No `venv` directory or any indication that a virtual environment was created, nor any record (e.g., `requirements.txt` installed packages, activation script, or logs) showing that the requirements were installed in the `code/` context. The artifact required by the task is missing.
- `T006a` (rejected 1x): The provided `code/schemas.py` is present but ends abruptly and contains a broken `get_required_columns` function that returns an undefined name (`REQU`). Moreover, the referenced `contracts/dataset.schema.yaml` file is missing, so we cannot confirm that the schema truly matches it. The artifact is therefore incomplete and does not satisfy the task requirements.
- `T026` (rejected 1x): The repository lacks the required output file `data/outputs/heatmap.png`, and the `generate_heatmap` function in `code/viz.py` is truncated (ends with an incomplete line `plt.figur`), meaning the heatmap generation code is not functional. The task’s deliverable is therefore not present.
- `T027` (rejected 1x): The required image `data/outputs/pcoa_sleep_quality.png` is absent, and the provided `code/viz.py` does not contain a complete implementation for generating a PCoA ordination plot colored by sleep quality (the file is truncated and only shows a heatmap function). The task’s core deliverable is therefore not satisfied.
- `T028` (rejected 1x): declared artifact(s) missing/empty/invalid: data/outputs/correlation_results.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

