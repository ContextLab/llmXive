# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings or screenshots were provided showing the required folders (`data/raw/`, `data/processed/`, `code/`, `outputs/`, `tests/`, `state/projects/`, `code/models/`). Without concrete evidence that these directories exist and are non‑empty, the task requirement is not satisfied.
- `T001b` (rejected 1x): The provided information contains no evidence that `__init__.py` files exist in the `code/`, `tests/`, or `code/utils/` directories; the artifact list is empty. To satisfy the task, these three `__init__.py` files must be present and non‑empty in the repository.
- `T002` (rejected 1x): The implementer provided no linting or formatting configuration files (e.g., .flake8, pyproject.toml with ruff/black settings, or CI scripts) and no evidence that ruff/flake8 and black have been set up. Without these artifacts, the requirement to configure linting and formatting tools is not satisfied.
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: outputs/run.log
- `T010` (rejected 1x): The provided `code/download_data.py` is truncated (the `load_dataset` call is incomplete) and does not contain a full implementation of the stratified sampling and HDF5 saving logic. Moreover, the expected output file `data/raw/oc20_sample.h5` is absent from the repository. Both the script and the required output are missing, so the task is not genuinely completed.
- `T014` (rejected 1x): The `align_entries` function is truncated and does not show the required exact‑string matching on `composition` and `surface_facet` nor the creation of an exclusion DataFrame; it only contains comments about the logic. Moreover, `outputs/exclusion_log.json` is a placeholder file with a single hard‑coded entry and a comment stating it will be generated later, rather than a real log produced by the script. The task’s core alignment and exclusion‑logging behavior is therefore not actually implemented.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

