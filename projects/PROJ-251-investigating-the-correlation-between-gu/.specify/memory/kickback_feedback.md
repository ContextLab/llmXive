# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): No ingestion script, validation logs, output CSV, correlation analysis results, or modeling code/artifacts were provided. The claim lacks any tangible files or data demonstrating that the NCBI SRA search, data filtering, validation, correlation calculations, or predictive modeling were actually performed.
- `T001` (rejected 1x): No directory listings or file system evidence were provided showing that the required folders (`code/`, `data/raw`, `data/processed`, `data/results`, `specs/001-investigating-the-correlation-between-gu/contracts/`) actually exist; without such artifacts the claim cannot be confirmed.
- `T039` (rejected 1x): No evidence of a ruff check, black formatting, or any modifications to files in the `code/` directory is provided; the required artifact (a clean, lint‑free, black‑formatted codebase) is missing. The implementer must run the tools, fix all reported issues, and commit the updated files as proof.
- `T001a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008a` (rejected 1x): No `.env` template file was presented; there is no evidence of a file containing placeholders for `SRA_TOKEN` and `DATA_SOURCE_URL`. The required artifact is missing, so the task is not satisfied.
- `T011a` (rejected 1x): No script, function, or data files were presented that actually fetch the pre‑processed OTU table and serology metadata for the SRP accession series, nor any output showing the retrieved dataset. Consequently the required artifact is missing.
- `T019a` (rejected 1x): No artifact such as a new CSV file (e.g., `cleared_with_diversity_normalized.csv` or similar) showing the relative abundance conversion was provided. Consequently, there is no evidence that `cleared_with_diversity.csv` was transformed to relative abundances, nor any code or output confirming the operation. The required output is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

