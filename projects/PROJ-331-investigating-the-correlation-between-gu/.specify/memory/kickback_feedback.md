# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The task's required artifacts `data/raw/open_asv.csv` and `data/raw/open_clinical.parquet` are both MISSING, so there is nothing to validate and no evidence that `python -m code.src.pipeline.ingest` exited 0 or logged SHA-256 checksums of real files. The ingest module and tests exist and look reasonable, but no test-pass or run evidence was supplied, and the verification criterion (checksums of the actual raw files) cannot be met without the files themselves.
- `T002` (rejected 1x): The required outputs `data/processed/filtered_samples.parquet` and `data/processed/clr_abundances.parquet` are MISSING from disk, and there is no execution evidence (test run logs, generated summaries) that `run_preprocess` was ever executed successfully on real data. Additionally, `cap_taxa_by_memory` is implemented so that any caller-supplied `max_taxa != 100` silently skips subsampling entirely, which does not faithfully implement the FR-010 RAM-budget guard (the test only works around it by calling the private `_cap_impl` directly). The implementer must run the pipeline to produce the two
- `T004` (rejected 1x): Requested task execution failed; rerun successfully: code/src/pipeline/correlation.py exit=1

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

