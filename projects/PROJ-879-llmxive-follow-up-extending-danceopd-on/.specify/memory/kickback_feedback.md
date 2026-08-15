# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013b` (rejected 1x): No code, logs, or dataset modifications were presented that demonstrate detection of undefined routing paths, counting/logging of such occurrences, and exclusion of those samples from the final output. The required artifact (implementation and evidence of the exclusion behavior) is missing.
- `T014` (rejected 1x): The `data/processed/teacher_routing_dataset.parquet` file does not exist, so the required output artifact is missing. Additionally, the provided `code/00_data_extraction.py` is truncated and does not show the final logic that writes the extracted columns to the parquet file. The task therefore remains unfinished.
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/unit/test_tree_training.py
- `T030` (rejected 1x): No artifact containing computed FID or CLIP scores for the full dataset is provided, nor any script, log, or report showing the comparison between tree‑generated images and teacher‑baseline images. Consequently the requirement to compute and present these metrics on the entire dataset is not satisfied.
- `T016b` (rejected 1x): No `teacher_routing_dataset.parquet` file or any inspection results are provided, and there is no evidence (e.g., a script output, summary table, or data snippet) showing that the dataset contains samples from both ImageNet‑1K and LAION‑400M sources. The required artifact and its validation are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

