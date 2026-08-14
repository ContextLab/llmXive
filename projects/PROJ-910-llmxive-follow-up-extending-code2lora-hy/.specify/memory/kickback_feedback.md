# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): The submission provides no evidence of the required `data/raw/`, `data/processed/`, or `data/adapters/` directories, nor any `.gitkeep` files within them. Without visible artifacts confirming these directories exist and contain the placeholder files, the task requirement is not satisfied.
- `T016` (rejected 1x): The provided evidence contains only the task description and project requirements, but lacks the actual `ast_parser.py` file or any code snippet demonstrating the implementation of the control-flow logic. Without seeing the file content, it is impossible to verify if the logic to skip malformed files, the specific logging calls using the T006 handler, and the `continue` statement for FR-007 are genuinely implemented rather than just described.
- `T017` (rejected 1x): No evidence of a modified `adapter_generator.py` containing a RAM‑usage check that aborts when usage exceeds 7 GB and logs the required error (FR‑008) was provided. The artifact is missing, so the task is not verified as completed.
- `T018` (rejected 1x): No evidence of a modified `adapter_generator.py` containing checkpoint validation logic is provided; the required code artifact is missing, so we cannot confirm that the abort‑on‑incompatible‑base‑model behavior was implemented.
- `T021` (rejected 1x): The provided `code/evaluation/runner.py` is incomplete (truncated after the adapter‑loading stub) and does not contain logic to run the model on the RepoPeftBench tasks, compute exact‑match scores, or write `data/results/ast_scores.csv`. Moreover, the required `ast_scores.csv` file is absent. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

