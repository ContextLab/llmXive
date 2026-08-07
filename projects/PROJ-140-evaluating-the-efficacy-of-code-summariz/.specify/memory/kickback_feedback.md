# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018a` (rejected 1x): No `contracts/api_participant.md` file or its contents were provided; therefore the required API contract (endpoints, request/response schemas, session management details) is missing. The implementer must create the markdown file with the full specification.
- `T018b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/ParticipantForm.jsx
- `T018c` (rejected 1x): The required file `backend/src/api/participant.py` (or an equivalent implementation) is missing from the repository, so no code handling submissions, session state, or Latin‑square assignment is present. The task’s core artifact is absent, making the implementation incomplete.
- `T012a` (rejected 1x): The latency calibrator script exists, but the required startup files (`backend/src/main.py` or `frontend/src/App.jsx`) are missing, and there is no evidence that the calibrator is imported or executed at application launch. Integration into the startup flow has not been demonstrated.
- `T016` (rejected 1x): The required output file `data/interaction_logs/anonymized_logs.csv` does not exist, and the provided `code/utils/anonymize_logs.py` is incomplete (truncated) with no evident entry‑point that reads raw logs and writes the anonymized CSV, so the task’s core requirement is unmet.
- `T019` (rejected 1x): No evidence of a `data/consent/` directory, a `.gitignore` entry excluding it, or any script/command that sets file permissions to `chmod 600` is provided. The implementer’s claim cannot be verified without these artifacts.
- `T030` (rejected 1x): declared artifact(s) missing/empty/invalid: github/workflows/test_reproducibility.yml
- `T031` (rejected 1x): declared artifact(s) missing/empty/invalid: data/reproducibility_package_v1.0.tar.gz, data/analysis_results/results.csv, data/interaction_logs/anonymized_logs.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

