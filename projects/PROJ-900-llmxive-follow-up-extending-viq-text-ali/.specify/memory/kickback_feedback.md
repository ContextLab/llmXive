# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T036` (rejected 1x): The response only shows a fragment of an updated spec, but no actual Decision Record documents or a verifiable `spec.md` file are provided. Without concrete artifacts confirming that the decision records were created and the spec file was updated, the task requirements are not satisfied. The next implementer must supply the full decision record files and the updated `spec.md` containing the documented deviations.
- `T036a` (rejected 1x): No markdown file at `specs/001-viq-resolution-invariance/decisions/001-chestx14-exclusion.md` was presented; without the file we cannot confirm it contains the required context, decision, and consequences. The task’s core deliverable is therefore missing.
- `T036b` (rejected 1x): No markdown file at `specs/001-viq-resolution-invariance/decisions/002-native-ground-truth-test.md` was presented; the claim lacks any evidence of the required document’s existence or content. The task remains undone until the specified decision record file is provided.
- `T036c` (rejected 1x): The provided spec excerpt shows FR‑003 updated to exclude ChestX‑ray14, FR‑004 updated to require native 1024×1024 ground truth, and SC‑005 updated to require a paired t‑test or Wilcoxon test. However, there is no evidence that the change was also applied to US‑2 (the removal of ChestX‑ray14 from that use‑case), and no actual `specs/001-viq-resolution-invariance/spec.md` file is presented to confirm the edits exist on disk. The implementer must supply the updated spec file showing the US‑2 change (or confirm its absence) to complete the task.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

