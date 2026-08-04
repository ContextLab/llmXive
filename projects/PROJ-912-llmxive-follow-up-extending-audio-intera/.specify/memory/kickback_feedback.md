# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001d` (rejected 1x): No `state/__init__.py` file was presented in the evidence, and no content was shown to confirm its existence or that it contains appropriate package initialization code. The required artifact is therefore missing.
- `T008a` (rejected 1x): declared artifact(s) missing/empty/invalid: github/workflows/ci.yml
- `T008b` (rejected 1x): The implementer provided only a feature specification for audio model compression, with no CI configuration files, scripts, or documentation showing environment variables for resource limits. No artifact related to “Configure CI runner environment variables for resource limits” is present.
- `T020` (rejected 1x): The repository contains a partially implemented `code/data/loader.py`, but the required output file `data/processed/subtle_cue_subset.parquet` is absent, and the checksum verification logic does not actually compare stored and computed checksums. Consequently the task’s core deliverables are not fulfilled.
- `T026` (rejected 1x): The implementer provided only the high‑level feature specification and user stories; there is no code, configuration, or log files showing that inference latency and RAM usage are actually being recorded. No logging implementation, test output, or documentation of the added logging was supplied, so the requirement to “Add logging for inference performance and resource usage” is not met.
- `T029` (rejected 1x): The `code/analysis/robustness_curve.py` file is truncated and the `save_correlation_data` function is incomplete (the `mkdir` call is cut off and no JSON writing logic is present). Moreover, the required output file `data/processed/correlation_data.json` does not exist on disk. Consequently, the task’s requirement to produce the raw correlation data JSON is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

