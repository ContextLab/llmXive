# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required project directory `projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat/` being created is provided; the implementer did not supply any artifact (e.g., a directory listing, screenshot, or log) confirming the `mkdir -p` command succeeded. The task remains unverified.
- `T001b` (rejected 1x): No evidence was presented that a `code/` directory actually exists (e.g., a directory listing, screenshot, or file path confirmation). Without such proof, we cannot verify that the required `mkdir -p code` command was executed. The implementer must provide concrete proof that the `code/` directory was created.
- `T001c` (rejected 1x): No evidence was presented that a `tests/` directory actually exists in the repository; the implementer provided no file listing, screenshots, or other proof of the `mkdir -p tests` command having been run. Without such artifact, the task requirement is not satisfied.
- `T001d` (rejected 1x): No evidence was provided showing that the `data/`, `state/`, and `docs/` directories were actually created; the implementer’s claim is unsubstantiated. The required directory artifacts are missing from the supplied information.
- `T001f` (rejected 1x): No README.md file or its contents were provided in the evidence; therefore we cannot confirm that a non‑empty project overview and quickstart instructions exist. The required artifact is missing.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: code/config.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

