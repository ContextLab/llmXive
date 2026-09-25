# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings, screenshots, or command output were provided to demonstrate that the required folders (`code/`, `data/`, `data/raw/`, `data/processed/`, `data/analysis/`, `tests/`, `contracts/`, `state/`) actually exist. Without concrete evidence the claim cannot be verified.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- `T006a` (rejected 1x): The required schema file `contracts/network_schema.schema.yaml` is missing (no `schema.yaml` present), and the referenced CSV `data/raw/networks.csv` also does not exist, so the task’s deliverable is not provided.
- `T006b` (rejected 1x): The required schema file `contracts/energy_schema.schema.yaml` does not exist, and the referenced data file `data/processed/energy_decay.csv` is also missing, so the task’s deliverable is not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

