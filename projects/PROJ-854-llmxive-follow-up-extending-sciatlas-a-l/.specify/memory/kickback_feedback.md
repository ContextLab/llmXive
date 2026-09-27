# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012c` (rejected 1x): No spec.md or plan.md files were provided, and there is no evidence that any occurrences of “PubGraph” were replaced with “OpenAlex-derived Subgraph” or “OpenAlex”. Without the actual edited documents, the requirement cannot be confirmed.
- `T040` (rejected 1x): The provided `src/services/ingest.py` still uses `pyalex` and a custom sampling routine; it never calls `datasets.load_dataset(..., streaming=True)` nor specifies the required `fields` and `filters`, nor streams nodes directly into the graph with a memory buffer limit. Additionally, the required fallback cache file `data/raw/cache.parquet` is missing, and there is no RuntimeError handling as specified.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

