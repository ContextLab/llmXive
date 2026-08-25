# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of a `code/` directory or an `__init__.py` file was provided; the prompt contains no artifact listing or file contents to verify that the required structure exists. The implementer must add the `code/` folder with an `__init__.py` (and any other expected sub‑directories) to satisfy the task.
- `T001b` (rejected 1x): No evidence of a `data/` folder with the required sub‑directories (`raw/`, `processed/`, `results/`) or a `data/.gitkeep` file is present; the implementer did not provide any artifact confirming the directory structure was created.
- `T011` (rejected 1x): The required file `tests/unit/test_extraction.py` does not exist in the repository, so no unit test verifying parsing of inequalities and effect sizes is present. The task’s core artifact is missing.
- `T012` (rejected 1x): The required artifact `tests/integration/test_pipeline_us1.py` does not exist, so no integration test is present to verify the 10‑pair subset pipeline behavior. The task cannot be considered fulfilled until this file is added with the appropriate test logic.
- `T014` (rejected 1x): The provided `code/01_fetch_and_match.py` ends abruptly (truncated at `def is_theoretic`) and contains no implementation of the required filtering (case‑study, theoretical paper, >20 % N change) nor any code that writes an `exclusion_reason` column or creates `data/raw/exclusion_log.csv`. The log file itself is absent. Consequently the task’s filtering and logging requirements are not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

