# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000` (rejected 1x): No `research/validation_report.json` file or any other evidence of a reference‑validation run is present. The task required executing the Reference‑Validator Agent on the Lee & See (2004) and Langer (1975) citations and producing a JSON report with validation status and title‑overlap scores, but no such artifact or its contents are available. The implementer must generate and provide the specified JSON file.
- `T001` (rejected 1x): No `research.md` file was provided, and there is no evidence of a table containing the required columns (Effect Size (f), Alpha, Target Power, Required N, Calculated N) or any documented power analysis or literature review. The task’s core artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

