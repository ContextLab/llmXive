# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): No `src/ingestion/downloader.py` file or its contents were provided; without the script we cannot verify that it uses `datasets.load_dataset(..., streaming=True)` to fetch verified HuggingFace/UCI URLs. The required artifact is missing.
- `T014` (rejected 1x): No `src/ingestion/profiler.py` file or its contents were provided; thus we cannot verify that the script computes the condition number, Breusch‑Pagan statistic, and Cook’s distance, nor that it handles datasets larger than 7 GB by subsampling. The required artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

