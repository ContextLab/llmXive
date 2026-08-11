# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005a` (rejected 1x): The repository lacks the required `data/derived/synthetic_queries_warmup.json` file (it is missing), and the shown `code/data/generator.py` does not contain any implementation that creates a 100‑query warm‑up set. Consequently the deliverable specified in the task is not present.
- `T010` (rejected 1x): No `state/manifest.json` file or `state/hashes/` directory was provided, and there is no evidence that SHA‑256 hashes for files in `data/` and `code/` were computed. The required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

