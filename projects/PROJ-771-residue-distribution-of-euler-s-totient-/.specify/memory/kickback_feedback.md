# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was provided that a `code/` directory exists in the repository; the artifact list is empty, so the required directory creation cannot be confirmed.
- `T001b` (rejected 1x): No evidence of the required `data/raw/` and `data/processed/` directories being present (e.g., no directory listings, creation logs, or files inside them) is provided; therefore the claim that the task is complete cannot be verified. The implementer must create the two directories and supply proof (e.g., a file tree snapshot or command output).
- `T001c` (rejected 1x): No evidence of the required `results/plots/` and `results/reports/` directories was provided; the claim lacks any artifact showing that these folders were created (e.g., a directory listing or screenshot). The implementer must supply proof that the two directories exist in the repository.
- `T001d` (rejected 1x): No evidence of the required `tests/unit/` and `tests/integration/` directories is provided; the artifact list contains no such paths, so we cannot verify that the directories were created. The implementer must add the two directories (with at least placeholder files if desired) to satisfy the task.
- `T014` (rejected 1x): No code, configuration, or log files were provided that implement the required error‑handling logic, nor any evidence (e.g., unit tests, screenshots, commit diff) showing that the sieve failure/overflow case logs the offending $n$ before any data‑save step. The artifact needed to satisfy the task is missing.
- `T013` (rejected 1x): No `data/raw/residues_{prime}_{N}.json` file (or any JSON serialization of a `ResidueDataset`) was presented, and there is no evidence that raw residue counts were saved as required. The implementer provided only a textual description without the actual artifact, so the task’s deliverable is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

