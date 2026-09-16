# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a#1` (rejected 1x): No evidence of the required `data/raw/` and `data/derived/` directories is present in the provided artifacts; the claim lacks any file listings, screenshots, or other proof that the directories exist and are non‑empty. The next implementer must create the two directories and provide a verification artifact (e.g., a directory tree listing).
- `T009` (rejected 1x): No configuration files, scripts, or documentation for managing dataset paths and random seeds are present in the provided evidence; the implementer did not supply the required environment‑configuration artifacts. The task therefore remains unfinished.
- `T025` (rejected 1x): No `scaling_factor.txt` file is present in the provided evidence, so the required artifact does not exist (or is empty). Consequently the task of writing the optimal scaling factor and its confidence interval has not been fulfilled.
- `T060` (rejected 1x): No `docs/benchmark_report.md`, `docs/correlation_report.md`, or `docs/review_response.md` files were provided or referenced; without these actual documentation artifacts present, the claimed documentation update cannot be verified as completed. The next implementer should add the three markdown files in the `docs/` directory with the appropriate content.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

