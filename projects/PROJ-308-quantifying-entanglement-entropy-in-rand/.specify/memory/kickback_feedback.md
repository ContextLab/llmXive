# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000` (rejected 1x): No `research.md` file was presented in the `specs/PROJ-308-001-quantifying-entanglement/` directory, nor any content from it. The required document is missing, so the task is not satisfied.
- `T001` (rejected 1x): No directory structure was shown or listed in the provided evidence; the response only contains a feature specification and user stories, with no concrete creation of any folders under `projects/PROJ-308-quantifying-entanglement-entropy-in-rand/`. The required directories are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

