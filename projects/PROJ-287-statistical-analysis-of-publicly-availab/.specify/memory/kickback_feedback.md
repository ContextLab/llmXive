# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: src/models/entities.py
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/fetch/pubmed_fetcher.py
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/preprocess/tokenizer.py
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/preprocess/filter.py
- `T017` (rejected 1x): The required `results/manifest.json` file does not exist, so the requested fields (`arxiv_fetch_status`, `pubmed_fetch_status`, and data checksums) cannot be verified or present. The implementer must create the manifest file and populate it with the specified entries.
- `T021` (rejected 1x): declared artifact(s) missing/empty/invalid: src/models/lda/validator.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

