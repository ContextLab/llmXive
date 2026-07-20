# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was presented showing that the directories `projects/PROJ-096-exploring-the-role-of-network-topology-o/code/utils` and `projects/PROJ-096-exploring-the-role-of-network-topology-o/code/data` actually exist (or were created). The implementer must provide a file‑system listing, screenshot, or command output confirming the presence of those directories.
- `T001b` (rejected 1x): No directory listings or screenshots were provided to show that `data/processed`, `data/checksums`, and `data/raw` actually exist under `projects/PROJ-096-exploring-the-role-of-network-topology-o/`. Without concrete evidence of these folders being created, the task requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

