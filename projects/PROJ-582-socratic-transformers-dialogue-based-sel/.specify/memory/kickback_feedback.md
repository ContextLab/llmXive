# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/download.py
- `T050` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/critic_loader.py
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/static_extractor.py
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/generate_dialogue.py
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: src/train/lora_config.py
- `T021` (rejected 1x): declared artifact(s) missing/empty/invalid: src/train/train_loop.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

