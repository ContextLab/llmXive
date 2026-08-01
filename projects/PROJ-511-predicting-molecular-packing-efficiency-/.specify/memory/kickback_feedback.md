# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007` (rejected 1x): No code files, scripts, or data artifacts were provided to demonstrate that base data‑loading utilities for CIF parsing and SMILES generation exist in the `code/` directory. Consequently, we cannot verify that a CSV with ≥ 500 rows, SMILES generation, or failure logging was implemented. The required implementation is missing.
- `T008` (rejected 1x): No code artifacts were presented showing modifications in the `code/` directory that implement error handling for corrupt CIF files or missing metadata. Without files, functions, or logs demonstrating such handling, the requirement cannot be confirmed as satisfied. The next implementer must add and provide the actual code (e.g., try/except blocks, validation checks, logging of failed CIFs, fallback SMILES generation flags) located in `code/`.
- `T009` (rejected 1x): No configuration file (e.g., `.env`, `config.yaml`, or similar) defining the COD download URL and the HuggingFace model path was found in the `code/` directory, nor any documentation or code that sets these values. The required environment configuration artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

