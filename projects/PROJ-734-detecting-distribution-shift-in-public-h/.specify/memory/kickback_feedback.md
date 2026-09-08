# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005` (rejected 1x): The required `contracts/config.schema.yaml` file is absent, and `code/main.py` never applies the `PipelineConfig` pydantic model to validate the loaded configuration (it simply returns a dict). Both the schema artifact and actual validation logic are missing.
- `T012a` (rejected 1x): The `data/raw/fluview_ili.csv` file is missing, and the download script uses a GitHub mirror as the primary URL instead of the canonical CDC source, violating the task’s “no third‑party mirrors” rule. The metadata also contains a placeholder hash, indicating the file was never actually retrieved.
- `T012b` (rejected 1x): The required `data/raw/ground_truth_events.csv` file does not exist, and the provided `download_data.py` does not fetch a ground‑truth CSV from the canonical CDC source but instead derives events from the FluView data (and even uses a non‑CDC mirror for FluView). This violates the “no fallback” rule and fails to produce the specified output file.
- `T016` (rejected 1x): The required `data/raw/ground_truth_events.csv` file is absent, so the loader cannot be exercised, and the posted `code/evaluate.py` snippet is incomplete (truncated) and shows no concrete implementation of the ±2‑week tolerance matching or a function that actually checks the ground‑truth source against the URL whitelist. The task’s core requirements are therefore not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

