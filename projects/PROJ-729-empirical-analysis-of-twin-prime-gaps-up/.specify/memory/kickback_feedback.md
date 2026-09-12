# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The `data/raw/twin_primes.csv` file does not exist, and the provided `code/generate_primes.py` is truncated (ends abruptly before writing any output), so it cannot produce the required CSV with the correct columns and values. The task’s verification conditions are therefore unmet.
- `T013b` (rejected 1x): No code, script, or console log showing the computation of the Hardy‑Littlewood expected twin‑prime count and the deviation percentage is present. The required artifact (evidence of the calculation and logged deviation) is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

