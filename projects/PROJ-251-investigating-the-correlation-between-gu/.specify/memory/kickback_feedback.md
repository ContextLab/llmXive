# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011b` (rejected 1x): No synthetic dataset file, script, or description was provided; the evidence contains only the original user story specifications, with no generated data or code to create it. The required artifact—a non‑empty synthetic dataset (e.g., CSV/TSV with microbiome OTU abundances and serology metadata) – is missing.
- `T011d` (rejected 1x): No code, data files, or analysis outputs were supplied; the claim provides only the original specification without any ingestion script, validated CSV, correlation results, or modeling artifacts required by the user stories. Consequently, the required deliverables are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

