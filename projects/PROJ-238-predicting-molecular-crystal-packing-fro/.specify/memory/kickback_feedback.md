# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): No `utils/descriptors.py` file or any code implementing the six molecular descriptor calculations is present; the submission provides no artifact to verify that volume, surface area, dipole, H‑bond acceptor/donor counts, and polar surface area are actually computed. The required implementation is missing.
- `T015` (rejected 1x): No code, script, notebook, or data file was provided that demonstrates the calculation of `packing_coefficient = V_mol / V_cell` nor the filtering of values outside the [0, 1] range. Without such artifacts, we cannot confirm the requirement was implemented.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

