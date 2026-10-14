# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The script ingests the **Lipophilicity** dataset via `skfp.datasets.moleculenet.load_lipophilicity` (4200 records) rather than the required **ESOL** dataset from the specified deepchem S3 URL — the `--url` argument is parsed but never used, so `data/raw/esol.csv` actually contains Lipophilicity data mislabeled as ESOL. Additionally, the required "chunked sparse-matrix fallback" for processing is entirely absent from the code, and the exclusion log contains duplicated entries (the same 5 SMILES written twice) from repeated appends, indicating the log/checksum append logic isn't idempotent. The

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

