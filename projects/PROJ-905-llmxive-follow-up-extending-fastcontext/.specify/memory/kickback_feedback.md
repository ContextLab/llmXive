# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007b` (rejected 1x): The repository contains a partially‑written `code/annotation_extractor.py` that ends abruptly (the loop body is incomplete and the file is truncated), and the required output file `data/raw/ground_truth_annotations.csv` does not exist. Consequently the script does not actually extract the annotations nor produce the CSV with `repo_id`, `issue_id`, and `ground_truth_file_paths` as specified. The implementer must finish the extractor logic and ensure the CSV is generated.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

