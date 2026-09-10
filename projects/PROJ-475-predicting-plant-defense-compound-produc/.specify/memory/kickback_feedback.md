# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The provided `code/data/ingestion.py` focuses on fetching compound data and does not implement the required logic for fetching or mocking VCF data nor does it write `data/raw/genomic_vcf.json`. Moreover, the expected output file `data/raw/genomic_vcf.json` is missing, and there is no evidence that the post‑fetch disk‑usage check (T008) is invoked. The task’s core requirement is therefore unmet.
- `T011` (rejected 1x): The provided `code/data/ingestion.py` contains logic for fetching compound data and does not implement the required environmental data fetching/generation nor produce `data/raw/env_data.json`. Moreover, the `env_data.json` file is missing, and there is no call to the T008 disk‑usage check. The task’s core requirement is therefore unmet.
- `T012` (rejected 1x): The required output file `data/raw/compound_data.json` does not exist, and there is no evidence that the script invokes T008 to verify disk usage after fetching or generating data. The implementation therefore does not satisfy the task’s output and post‑check requirements.
- `T015` (rejected 1x): The `code/data/preprocessing.py` file is truncated (ends mid‑statement) and does not contain the full logic to write `data/processed/filtered.csv` or to log exclusion decisions as required. Moreover, the expected output file `data/processed/filtered.csv` is absent. The task’s core requirements are therefore not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

