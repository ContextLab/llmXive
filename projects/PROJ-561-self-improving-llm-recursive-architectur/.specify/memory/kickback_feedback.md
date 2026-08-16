# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): No `config.py` file was presented in the evidence, and therefore there is nothing to load or check for the required hyperparameters, parameter‑increase constraint, or path definitions. The implementer must supply a non‑empty `config.py` that defines `lr=5e-5`, `bs=4`, a seed, enforces the ≤30 % parameter‑increase limit, and includes the specified path variables, and it must load without error and assert the default values.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

