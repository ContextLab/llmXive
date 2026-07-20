# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T023` (rejected 1x): No code, data file, test results, or any other artifact demonstrating the added logic for simulating response times and 1‑5 Likert comprehension ratings is present. Consequently there is no evidence that the distribution constraint (no gaps > 5 s) has been implemented or verified. The required implementation and its validation are missing.
- `T028` (rejected 1x): No merged dataset containing at least 200 records is present, nor any script or notebook showing the logic that combines simulated and real student data and validates the impact of the `data_source` field. The claim lacks any concrete artifact (code, data file, or validation output) to demonstrate that the required functionality was implemented.
- `T029` (rejected 1x): No results markdown file was provided; the claim lacks any artifact showing significance testing (p < 0.05) or confidence‑interval width validation required by T029. The implementer must supply a non‑empty markdown document containing the statistical test results and CI checks.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

