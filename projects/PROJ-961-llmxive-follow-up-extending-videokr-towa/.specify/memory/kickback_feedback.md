# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required `code/`, `tests/`, or `data/` directories (or any files within them) was provided; the claim lacks any tangible artifact confirming their creation.
- `T001b` (rejected 1x): No evidence was provided that the required subdirectories `code/ingest/`, `code/analysis/`, and `code/utils/` actually exist in the repository; the response contains only a textual description of the feature specification without any file listings or directory structures. The implementer must create and show these three non‑empty directories.
- `T001c` (rejected 1x): No evidence was provided showing that the `tests/unit/` and `tests/integration/` directories actually exist in the repository; the claim is unsupported and the required subdirectories are not demonstrated.
- `T008a` (rejected 1x): No `.gitkeep` file in `data/raw/` was shown or described; the implementer provided no artifact or proof that the file exists, so the required output is missing.
- `T008b` (rejected 1x): No evidence of a `.gitkeep` file in the `data/processed/` directory is provided; the implementer did not supply the required artifact, so the task is not verified as completed.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/annotated_videokr.csv
- `T015` (rejected 1x): No `annotate_graph.py` file containing a proactive two‑stage sampling implementation is provided, nor any benchmark or test showing the analysis finishes within 6 hours on a 2‑core runner. The claim lacks the required artifact and runtime evidence.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

