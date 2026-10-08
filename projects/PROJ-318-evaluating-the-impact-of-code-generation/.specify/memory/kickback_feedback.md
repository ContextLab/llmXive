# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018b` (rejected 1x): No `plan.md` content was provided, so we cannot confirm that the required statements were added, that references to “100 methods” were removed, or that “[deferred] methods” appears as specified. The artifact needed to verify the task is missing.
- `T035` (rejected 1x): The required `data/processed/results_with_scores.json` file is missing, and `data/processed/results_with_stats.json` was not produced. Moreover, `code/analyze.py` is incomplete (e.g., `run_wilcoxon_analysis` is truncated, no handling of `--step=stats`, and no code to write the stats file). The Wilcoxon test implementation and warning logic are therefore absent.
- `T037` (rejected 1x): The required artifacts `data/processed/results_with_stats.json` and `data/processed/final_report.json` are absent, and the provided `code/analyze.py` is incomplete (truncated before any reporting logic). Consequently, the task of verifying the JSON file, generating the final report, and running the analysis script has not been fulfilled.
- `T039` (rejected 1x): No updated README.md file was presented; the claim lacks any evidence of added installation instructions or usage examples, so the required artifact is missing.
- `T033` (rejected 1x): The required files `data/processed/results.json` and `data/processed/results_with_coverage.json` are missing, so the existence and non‑emptiness check fails. Moreover, the provided `code/analyze.py` is incomplete (truncated before the coverage‑score logic is fully implemented), so the parameter‑coverage calculation and output generation are not verified. The task therefore remains unfinished.
- `T040` (rejected 1x): No evidence of a modified or newly created `quickstart.md` was provided; the claim lacks the required artifact showing a step‑by‑step execution guide. The implementer must supply the updated `quickstart.md` file with the requested instructions.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

