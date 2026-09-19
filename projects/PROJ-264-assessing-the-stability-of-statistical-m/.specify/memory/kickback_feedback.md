# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T050` (rejected 1x): No execution logs, output files, or reports are provided showing a full pipeline run on three datasets (one <1k, one 1k‑10k, one >10k). Without concrete artifacts (e.g., console output, generated report, or saved results) the claim cannot be verified. The required evidence of the end‑to‑end smoke test is missing.
- `T051` (rejected 1x): The required artifact `results/memory_profile.log` does not exist, so the memory profiling step was not performed or its output was not saved as specified. The task’s core requirement—logging peak RSS memory usage—is unmet.
- `T052` (rejected 1x): No evidence of the smoke test being run twice, no recorded checksums of the output CSVs or final report, and no verification that they are identical. The required artifact (determinism verification results) is missing.
- `T053` (rejected 1x): The required `.github/workflows/ci.yml` file does not exist in the repository, so no workflow configuration can be verified for the specified triggers, timeout, or signal handling. The implementer must add the file with the correct settings.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

