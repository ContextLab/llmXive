# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T040a` (rejected 1x): The provided `code/09_literature_extraction.py` stops after fetching abstracts and does not contain the spaCy NER extraction, confidence filtering, median selection, or JSON writing required, and the expected output file `data/raw/literature_metadata.json` is absent. Consequently the script does not fulfill the specification.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

