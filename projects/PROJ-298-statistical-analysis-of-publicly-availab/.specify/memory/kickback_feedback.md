# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of a `projects/PROJ-298-statistical-analysis-of-publicly-availab/` directory (or any files within it) is provided; the response only contains a feature specification, not the required filesystem artifact. The required root directory is missing.
- `T007` (rejected 1x): The `code/data/generate_taxonomies.py` script exists but is truncated and does not actually produce the required output files. Both `data/events/reference_calendar.json` and `data/taxonomy/survey_2023.json` are missing from the repository, so the task’s deliverables are not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

