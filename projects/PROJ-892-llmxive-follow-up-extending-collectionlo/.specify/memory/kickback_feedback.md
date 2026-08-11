# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007b` (rejected 1x): The `data/models/adapter_fp16.safetensors` file is missing (size 0) and `state/artifacts.yaml` records a hash of an empty file. Moreover, `code/data_loader.py` contains only placeholder stubs and does not implement the required copy/rename‑and‑hash logic. The task’s core requirement is therefore not satisfied.
- `T009` (rejected 1x): The `data/models/adapter_fp16.safetensors` file is absent, and `code/data_loader.py` contains only stub functions (e.g., truncated `quantize_adapter_fp16_to_int8` and no implementation that loads the adapter, extracts per‑effect LoRA matrices, runs SVD, or writes `subspace_ranks.json`). Thus the required functionality is not actually provided.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

