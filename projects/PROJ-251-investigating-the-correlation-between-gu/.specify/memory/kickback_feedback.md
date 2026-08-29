# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): No ingestion script, output CSV, logs, or analysis results were provided; the claim lacks any tangible artifacts (code, data files, or result tables) required to demonstrate that SRA data were searched, filtered, validated, and that downstream correlation and modeling steps were performed. The implementer must supply the actual scripts and generated output files to satisfy the user stories.
- `T001` (rejected 1x): No directory listings or file system evidence were provided showing that the required folders (`code/`, `data/raw`, `data/processed`, `data/results`, `specs/001-investigating-the-correlation-between-gu/contracts/`) actually exist; without such artifacts the claim cannot be verified.
- `T039` (rejected 1x): No linting or formatting artifacts (e.g., ruff output logs, black diff reports, or updated, clean code files) are present to demonstrate that ruff checks were run and all issues were fixed. The required evidence of the codebase being lint‑checked and black‑formatted is missing.
- `T001a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008a` (rejected 1x): No `.env` template file was provided in the evidence; there is no file containing placeholders for `SRA_TOKEN` and `DATA_SOURCE_URL`, so the required artifact is missing.
- `T011a` (rejected 1x): No code, script, or fetched data files are provided to demonstrate that the pre‑processed OTU table and serology metadata for the SRP accession series have been retrieved; the required artifact (a data ingestion implementation and its output) is missing.
- `T019a` (rejected 1x): No code, notebook, script, or data file was provided that performs or demonstrates conversion of the OTU table to relative abundances, nor any output showing the normalized values. The required artifact for task T019a is missing.
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: data/results/correlation_results.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

