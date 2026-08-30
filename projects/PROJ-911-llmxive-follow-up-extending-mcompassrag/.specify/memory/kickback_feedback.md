# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/graphs.json, data/processed/features.csv
- `T017` (rejected 1x): No code, configuration, or log files were provided that show logging of per‑document processing time, nor any evidence (e.g., log excerpts, test output) confirming that the processing time stays under the 60‑second limit. The required artifact (logging implementation and its verification) is missing.
- `T022` (rejected 1x): The `code/retrieval_sim.py` file is truncated and its `save_retrieval_scores` function is unfinished, and the required output file `data/results/retrieval_scores.csv` is missing from the repository. Without a complete implementation that writes the ranked results to the specified CSV, the task is not satisfied.
- `T023` (rejected 1x): declared artifact(s) missing/empty/invalid: data/results/retrieved_features.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

