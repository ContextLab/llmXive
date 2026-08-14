# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T038` (rejected 1x): The claim provides no actual `quickstart.md` or `research.md` files, nor any excerpts showing that `research.md` lists the selection rationale for DT vs GMM or the exact command‑line flags. Without these documents present and containing the required information, the documentation update task is not satisfied. The next implementer must add the two markdown files (or update the existing ones) and ensure `research.md` explicitly compares DT and GMM performance per T022 and lists the pipeline’s command‑line flags.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

