# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011a` (rejected 1x): The provided `code/data/schema_check.py` is truncated, does not pass `revision='main'` to `load_dataset`, and does not contain logic that raises a fatal `ValueError` when required columns are missing. Moreover, the expected output file `data/processed/schema_check.log` is absent. These issues mean the implementation does not fulfill the task’s specifications.
- `T011b` (rejected 1x): The repository lacks the required `data/raw/sn1_raw.parquet` file, and the provided `download.py` does not clearly implement the conditional “use streaming if size > 7 GB” (it forces `USE_STREAMING = True`). Moreover, the script is truncated before the actual download‑and‑save logic, so we cannot verify it writes the parquet file. These issues mean the task’s output and constraints are not satisfied.
- `T011c` (rejected 1x): The provided `code/data/mapping.py` is truncated and ends mid‑statement, so it does not contain a complete implementation (e.g., no code to write `intermediate_sn1.csv` or to log exclusions). Additionally, the required output files `data/processed/exclusion_raw.log` and `data/processed/intermediate_sn1.csv` are absent. The task’s mapping and cleaning logic is therefore not fully realized.
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/clean.log, data/processed/exclusion_raw.log, data/processed/exclusion_report.csv, data/processed/exclusion_mapped.json, schema.yaml
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/cleaned_sn1.csv, data/processed/success_rate.json
- `T028` (rejected 1x): The repository lacks the required input file `data/processed/cleaned_sn1.csv`, so the script cannot compute VIFs, and no `artifacts/collinearity_report.json` is present. Additionally, the provided `collinearity.py` is truncated and does not show the full VIF calculation and JSON generation logic. The task’s essential artifacts are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

