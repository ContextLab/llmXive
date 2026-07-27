# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was provided that a `src/services` directory was created; the only artifacts shown relate to a high‑level feature specification, not a filesystem change. The required directory is missing from the provided evidence.
- `T001c` (rejected 1x): No evidence of a `src/models` directory was presented; the claim provides only a description of higher‑level feature work and no filesystem artifact confirming the required directory exists (and is non‑empty). The implementer must create the `src/models` folder in the repository and show its presence.
- `T001d` (rejected 1x): No evidence was presented that a `src/utils` directory actually exists in the project; the implementer provided no file listing, screenshots, or other proof of its creation. The required artifact is therefore missing.
- `T001e` (rejected 1x): No evidence was provided that a `src/data-models` directory exists in the repository; the implementer did not supply a file‑system listing or any artifact confirming the directory was created. The required directory is therefore missing.
- `T001f` (rejected 1x): No evidence was provided that a `tests/unit` directory exists in the repository; the implementer did not supply a directory listing, screenshot, or any file showing the creation of `tests/unit`. Without this artifact, the requirement to create the directory is not satisfied.
- `T001g` (rejected 1x): No evidence was provided that a `tests/contract` directory exists in the repository; the artifact list is empty, so the required directory was not created.
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data-models.py
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: src/cli/main.py
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: src/services/download.py
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/services/filter.py
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: src/models/vlm.py
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: src/services/scoring.py
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: src/services/scoring.py
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: src/services/scoring.py
- `T021` (rejected 1x): declared artifact(s) missing/empty/invalid: src/cli/main.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

