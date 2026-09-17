# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004a` (rejected 1x): No directory or `.gitkeep` file was presented in the provided evidence; without seeing the `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/raw/` folder containing a `.gitkeep` file, the requirement is not satisfied.
- `T004b` (rejected 1x): No evidence of the required directory `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/processed/` or a `.gitkeep` file within it was provided; the claim cannot be verified. The implementer must add the actual folder and placeholder file to satisfy the task.
- `T004c` (rejected 1x): No evidence of the required directory `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/artifacts/` or a `.gitkeep` file inside it was provided; the claim cannot be verified. The implementer must add the folder and include a non‑empty `.gitkeep` file.
- `T005` (rejected 1x): The required state file `state/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml` does not exist, and the provided `state_manager.py` (as shown) contains only hash‑calculation utilities without any logic that writes or updates that YAML file. The task’s core requirement—to update the YAML with content hashes and timestamps—is therefore unmet.
- `T008` (rejected 1x): The implementer provided no code, configuration files, or documentation defining a `DatasetUnavailableError` exception or the surrounding error‑handling infrastructure. Since the required artifact is missing entirely, the task is not satisfied.
- `T009` (rejected 1x): No code, scripts, or dataset files were provided to demonstrate the symbolic perception pipeline, the transformed “Symbolic‑Guava” JSON outputs, or any performance measurements (e.g., ≤150 ms per frame, full‑set runtime ≤4 h). Consequently the required artifact—an end‑to‑end CPU‑only transformation pipeline and its validated output—is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

