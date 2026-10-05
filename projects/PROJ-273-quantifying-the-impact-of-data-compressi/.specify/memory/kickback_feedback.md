# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T019` (rejected 1x): The required pipeline modules `src/data/fetch_logic.py` and `src/data/validation_logic.py` are absent, and the provided `src/data/fetch_loop.py` is only a partial, truncated implementation (ends mid‑function). The task’s core deliverables are therefore not present.
- `T019#1` (rejected 1x): declared artifact(s) missing/empty/invalid: src/compression/lossless.py
- `T021` (rejected 1x): declared artifact(s) missing/empty/invalid: src/compression/metrics.py
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: src/compression/main.py
- `T023` (rejected 1x): No code, data, or documentation was presented that implements the logic to flag compression levels with SNR degradation > 5 % as “unacceptable.” The required artifact (e.g., a function, script, or configuration change) is absent, so the task’s requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

