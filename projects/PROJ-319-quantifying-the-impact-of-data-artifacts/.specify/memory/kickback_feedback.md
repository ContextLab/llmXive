# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006` (rejected 1x): The repository contains a `code/synthetic/generator.py` file, but the required ground‑truth metadata file `data/synthetic/gt_metadata.json` does not exist, and there is no evidence that the script actually writes FITS images to `data/synthetic/synth_{id:03d}.fits`. Without the JSON file (and confirmed image output), the task’s core deliverables are missing.
- `T040` (rejected 1x): The repository lacks the required `data/synthetic/gt_metadata.json` file, and the provided `code/main.py` excerpt does not contain a `run_us2_pipeline` function (or any code that explicitly loads that metadata before computing asymmetry bias). Both the needed artifact and the code change are absent.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

