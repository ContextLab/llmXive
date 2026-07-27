# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004b` (rejected 1x): The provided `config.py` only loads and validates `global_seed` but never sets `numpy.random.seed`, `random.seed`, nor passes `random_state=seed` to the three NetworkX graph generators. Additionally, the required `config.yaml` file is missing, so the seed cannot even be loaded. Both the seed‑injection implementation and the configuration file are absent.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

