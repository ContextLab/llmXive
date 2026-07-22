# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019` (rejected 1x): The `code/eval_high_res.py` file exists but its content is truncated and does not show the full logic for loading 1024×1024 images, encoding them, and writing projected embeddings to `data/results/embeddings_high_res.h5`. Additionally, the required checkpoint `data/results/codebook_v0.pth` (and the output H5 file) are missing, so the script cannot be verified as functional. The implementation must be completed and the necessary artifacts provided.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

