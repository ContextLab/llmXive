# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The `verify_us1.py` script contains the verification logic but the required output file `data/results/us1_verification.json` is absent, and the `main()` function (which should loop over all runs) is incomplete/truncated, so the task’s full execution and result recording are not demonstrated.
- `T028` (rejected 1x): The `run_statistical_test` implementation is truncated and contains syntax errors (e.g., `pivot_data = pivo`), never reads `data/results/simulation_summary.csv`, never writes the required JSON output, and does not perform the bootstrap CI calculation. Moreover, the required input CSV and the expected result JSON file are missing from the repository.
- `T029c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/results/simulation_summary.csv
- `T029d` (rejected 1x): declared artifact(s) missing/empty/invalid: data/results/simulation_summary.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

