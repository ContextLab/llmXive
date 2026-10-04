# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of a `code/` directory being present (or its contents) is provided; without a visible directory or listing we cannot confirm the implementer actually created it. The required artifact is missing.
- `T001b` (rejected 1x): No evidence was provided showing that the `data/raw/` and `data/processed/` directories actually exist; the response contains no file listings, screenshots, or commands confirming their creation. The required artifact (the two directories) is therefore missing.
- `T001c` (rejected 1x): No evidence was provided that the `results/plots/` and `results/reports/` directories actually exist (e.g., a directory listing, command output, or screenshot). Without such proof, we cannot confirm the required directories were created.
- `T001d` (rejected 1x): No evidence of the required `tests/unit/` and `tests/integration/` directories is provided; the artifact list contains no such paths, so we cannot verify that the directories were actually created. The implementer must add the directories (and optionally a placeholder file) to the repository.
- `T014` (rejected 1x): No code, configuration, or log files were supplied that show error‑handling logic for the sieve, nor any evidence that the logging of the offending $n$ occurs before any data‑save step. Without such artifacts the requirement cannot be verified as met.
- `T013` (rejected 1x): No `data/raw/residues_{prime}_{N}.json` file (or code that creates it) is present, and there is no evidence of JSON serialization of a `ResidueDataset`. The required output artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

