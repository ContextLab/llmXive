# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T048` (rejected 1x): The pipeline runs, but `code/main.py` (and `fetch_experimental.py`) deliberately fall back to bundled CSV files when the Materials Project API key is missing or when the experimental URL is a `file://` path, and the provenance log `data/provenance/dft_queries.jsonl` shows zero API queries. This violates the task’s “FAIL LOUDLY on fetch errors — no synthetic/mock fallback is permitted” requirement, so the ingestion is not performed on real remote data as mandated.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

