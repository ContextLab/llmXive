# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005` (rejected 1x): No `utils/dedup.py` file (or any non‑empty implementation) is present in the provided artifacts, so the required deduplication utility for normalizing and de‑duplicating chemical formulas has not been delivered. The task remains unfinished.
- `T007` (rejected 1x): No evidence of the `data/raw/` and `data/processed/` directories or the required `.gitkeep` placeholder files was provided; without these artifacts the task requirement is not satisfied.
- `T008` (rejected 1x): No configuration files (e.g., .env, config.yaml, or Python settings) containing the Materials Project API key or dataset path definitions were provided; the claim lacks any tangible artifact demonstrating that environment configuration management has been set up. The required files must be added and contain the actual keys/paths for the task to be considered complete.
- `T012` (rejected 1x): No `features/descriptors.py` file is present, and no code implementing the listed atomic descriptors (Atomic Radius, Electronegativity, etc.) is provided. The claim lacks the required artifact, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

