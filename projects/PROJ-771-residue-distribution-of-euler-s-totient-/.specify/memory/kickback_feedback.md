# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was presented showing that a `code/` directory exists in the repository (e.g., a directory listing or file path). Without such proof, we cannot confirm the required artifact was created.
- `T001b` (rejected 1x): No evidence of the required `data/raw/` and `data/processed/` directories being created is provided; the artifact list is empty, so the claim that the directories exist cannot be verified. The implementer must create those directories (or provide proof they exist) to satisfy the task.
- `T001c` (rejected 1x): No evidence of the required `results/plots/` and `results/reports/` directories was provided; the claim lacks any artifact showing that these folders were created (e.g., a directory listing or screenshot). The implementer must supply proof that the two directories exist in the repository.
- `T001d` (rejected 1x): No evidence of the required `tests/unit/` and `tests/integration/` directories being present in the repository is provided; the artifact list is empty, so we cannot confirm the directories were actually created. The implementer must add these directories (and optionally placeholder files) to satisfy the task.
- `T030` (rejected 1x): No `quickstart.md` file or any documentation artifact was provided; the claim contains only feature specifications and test scenarios, but lacks the required markdown file with execution instructions for $N=5{,}000{,}000$. The task’s core deliverable is missing.
- `T031` (rejected 1x): No `run_analysis.py` file or any refactored code was provided; the evidence consists only of the task description and specifications, without the required artifact demonstrating a clean separation of orchestration logic. The implementer must supply the refactored `run_analysis.py` source code (non‑empty) for verification.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

