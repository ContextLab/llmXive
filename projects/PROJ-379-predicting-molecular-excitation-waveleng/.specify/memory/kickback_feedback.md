# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listing or evidence of the required folders (`data/raw`, `data/processed`, `code`, `tests`, `docs`) under `projects/PROJ-379-predicting-molecular-excitation-waveleng/` was provided, so we cannot confirm that the structure was actually created. The implementer must supply a file‑system snapshot, `tree` output, or similar proof that these directories exist and are non‑empty.
- `T001c` (rejected 1x): No `README.md` file or its contents were provided; therefore there is no evidence that a Quickstart section with environment setup, data fetching, and end‑to‑end pipeline instructions exists. The required artifact is missing.
- `T010` (rejected 1x): The provided `code/split.py` is truncated (the `scaffold_split` function ends abruptly and no code writes the split indices to `data/processed/split_indices.json`). Moreover, the required JSON file does not exist, and there is no explicit check that a scaffold appears in only one split. The implementation must be completed and the output file generated.
- `T025` (rejected 1x): No code, data, notebook, or output files were provided that demonstrate the application and verification of masking as required by task T025. Without any tangible artifact (e.g., a script that applies masking to the dataset and a report or logs confirming the mask was correctly applied and validated), the claim cannot be confirmed. The implementer must supply the masking implementation and evidence of its verification.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

