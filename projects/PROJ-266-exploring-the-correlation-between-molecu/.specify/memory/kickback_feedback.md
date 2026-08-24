# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000` (rejected 1x): No evidence of a `research.md` file in `specs/001-molecular-flexibility-permeability/` was provided, nor any content showing the required sections (Introduction, Methodology, Results, Discussion). The implementer must create the file with the specified template.
- `T008a` (rejected 1x): The submission provides no evidence of the `data/raw/` and `data/processed/` directories being created (no file listings, scripts, or commands are shown). Without such artifacts, the requirement to create the folder structure using OS path utilities is not satisfied. The next implementer must add the actual directory creation (e.g., a Python script using `os.makedirs` or a shell command) and verify the folders exist.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T001` (rejected 1x): No evidence of a `specs/001-molecular-flexibility-permeability/research.md` file was provided, nor any excerpt showing the required headers and placeholder text. Without the actual artifact, we cannot confirm the task was fulfilled. The implementer must add the file with the exact sections listed.
- `T002` (rejected 1x): No evidence of the required `code/`, `tests/`, or `data/` directories (or any files within them) was provided; without a directory listing or actual files, we cannot confirm that the project structure was created as specified. The implementer must supply the filesystem layout showing these three top‑level folders (and ideally non‑empty placeholder files) to satisfy the task.
- `T004` (rejected 1x): No linting or formatting configuration files (e.g., .flake8, pyproject.toml, setup.cfg) or setup scripts are present in the provided evidence, so the requirement to configure flake8/black is not satisfied. The implementer must add the appropriate configuration files and any integration steps (e.g., pre‑commit hooks) to complete the task.
- `T008c` (rejected 1x): No artifact (script, test output, or directory listing) was provided showing that `data/raw` and `data/processed` exist or that the required `assert` statements were executed. Consequently the requirement to verify the directory structure cannot be confirmed.
- `T009` (rejected 1x): The required output file `data/raw/chembl_raw.csv` does not exist, nor does the checksum file `state/pending/checksums.yaml`. Moreover, the provided `retrieval.py` snippet shows only fetching and record extraction functions and never writes a CSV or invokes the checksum utility. The task’s core deliverables are therefore missing.
- `T010` (rejected 1x): The repository contains a `preprocessing.py` script, but it does not create the required `data/processed/filtered_data.csv` nor invoke the checksum utility to produce `state/pending/checksums.yaml`. Both output files are missing, and the script lacks the final steps (CSV writing, protocol‑heterogeneity counting/reporting, checksum generation) required by the task.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

