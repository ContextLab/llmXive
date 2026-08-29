# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of a `projects/PROJ-008-psychology-research/` directory or any of its required sub‑folders/files is provided. The implementer did not supply the project structure, so the task’s core deliverable is missing.
- `T003` (rejected 1x): The implementer provided no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or `black` settings) nor any documentation showing that `ruff` and `black` have been set up and integrated into the project. Consequently, the required artifact for task T003 is missing.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/cleaned_studies.csv, data/raw/excluded_studies.log
- `T029` (rejected 1x): No code, configuration, or documentation was provided that shows the required conditional logic (suppressing subgroup/meta‑regression when total N < 10 and falling back to a descriptive synthesis). Without any artifact to inspect, we cannot confirm the feature was implemented. The missing deliverable is the implementation (e.g., function, script, or module) and evidence (tests or logs) demonstrating the N‑threshold behavior.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

