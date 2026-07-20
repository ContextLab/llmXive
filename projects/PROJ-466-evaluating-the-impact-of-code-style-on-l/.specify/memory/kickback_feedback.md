# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016a` (rejected 1x): The repository contains a `pipeline.py` with a generic `write_samples_atomic` function, but it never reads the buffer nor writes to `data/processed/samples_all.csv`, and the required `samples_all.csv` file does not exist. The task’s core requirement—producing the final `samples_all.csv` atomically—is therefore unmet.
- `T034` (rejected 1x): The required `code/analysis/collinearity_flag.json` file is missing, so the reporter cannot read the needed `flag` and `suggestion` keys. Moreover, the provided `reporter.py` is only partially shown and does not demonstrate the full PDF/HTML generation, sensitivity plot creation, survivorship bias section, bias/model‑incapability flags, or collinearity suggestion injection. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

