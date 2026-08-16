# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): The required `data/config/tract_lexicon.yaml` file is missing, causing the parser’s pre‑flight check to fail, and the expected output files `data/logs/exclusion_log.csv` and `data/processed/extracted_studies.csv` have not been created. Additionally, the provided `parser.py` is truncated and does not demonstrably implement the full extraction, narrative‑pool handling, and CSV generation described in the task.
- `T008c` (rejected 1x): The provided `code/analysis/tract_counting.py` is truncated (e.g., the `run_tract_counting` function ends abruptly and lacks a proper return or execution guard), so it cannot reliably read the CSV, apply harmonization, count tracts, and write `data/processed/tract_count.json`. Additionally, the required input CSV and output JSON files are absent, indicating the script has not been demonstrated to work end‑to‑end. The implementation must be completed and verified with the expected files.
- `T014` (rejected 1x): The required `data/processed/study_count.json` file is missing, so the script cannot read the mandatory `N` value at runtime. Without this file the implementation cannot satisfy the gate‑logic requirement, regardless of the code present in `meta_analysis.py`.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

