# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017a` (rejected 1x): No code, script, notebook, or data file showing that the timecourses from T014, T015, and T016 have been loaded and concatenated into a single NumPy array is present. The claim lacks any artifact (e.g., a `.npy` file, a Python function, or console output) demonstrating the required in‑memory combination, and there is no evidence that the prerequisite tasks’ outputs even exist. The implementer must provide the actual implementation and proof (e.g., a saved array file or reproducible code) that performs the combination.
- `T017b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/roi_timecourses.csv, schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

