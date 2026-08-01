# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001g` (rejected 1x): The required artifact `data/raw/conversations.jsonl` does not exist, so the implementer could not verify the presence of an `authenticity_score` field as required. The task remains unfinished until the file is provided and inspected.
- `T001d` (rejected 1x): declared artifact(s) missing/empty/invalid: src/analysis/validation.py, data/processed/hedge_gold_standard.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

