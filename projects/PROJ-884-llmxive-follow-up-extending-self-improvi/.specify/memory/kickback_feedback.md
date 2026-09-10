# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001c` (rejected 1x): No evidence was presented showing that a `tests/` directory with `unit` and `integration` sub‑directories exists, nor any proof (e.g., command output, script, or test) that they are writable. The implementer must create the directories and provide verification that they are present and have write permissions.
- `T008c` (rejected 1x): The repository lacks the required input file `data/processed/calibration_run.json` and the generated output `data/processed/calibrated_tdp.json`. The provided `generate_tdp_constant.py` is truncated and shows no code that writes the calibrated JSON to the expected path or overwrites `DEFAULT_TDP_WATTS` in `config.py`. The unit test only validates a temporary file and does not check the real output file or the config modification. These essential artifacts and behaviors are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

