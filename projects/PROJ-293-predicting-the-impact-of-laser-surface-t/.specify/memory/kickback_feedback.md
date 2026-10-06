# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T039a` (rejected 1x): No `research.md` file or its contents were provided, so we cannot confirm that it contains only verified static URLs/IDs and lacks any dynamic search logic. The required artifact and its verification evidence are missing.
- `T010` (rejected 1x): The `fetch_sources` function only checks for mock data and never attempts real OpenML/HuggingFace fetches, nor does it write the resulting DataFrame to `data/raw/aggregated_raw.csv`. The required output file is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

