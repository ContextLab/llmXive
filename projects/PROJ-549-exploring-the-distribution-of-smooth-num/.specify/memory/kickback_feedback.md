# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory `projects/PROJ-549-exploring-the-distribution-of-smooth-num/` or its subfolders (`code/`, `data/`, `tests/`, `state/`) was provided; without a visible file‑system listing or screenshots, we cannot confirm the structure exists. The implementer must supply proof that the project folder and the four subdirectories have been created and are non‑empty.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `.pylintrc`, `pyproject.toml` with Black settings) or related CI setup were presented for the `code/` directory, so the required artifact is missing.
- `T012` (rejected 1x): The provided `code/sieve.py` is truncated (ends abruptly at `for i in rang`) and does not contain the full segmented‑sieve implementation, progress logging, runtime measurement, CSV writing, or a final count log. Moreover, the required output file `data/primes_1e9.csv` is absent. These missing pieces mean the task’s specifications are not satisfied.
- `T013` (rejected 1x): The `code/validate_sieve.py` script is present, but the required input `data/primes_1e9.csv` is missing, so the script cannot run, and there is no validation report or checksum output to show that the verification was performed. The task therefore lacks the essential artifact and execution evidence.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

