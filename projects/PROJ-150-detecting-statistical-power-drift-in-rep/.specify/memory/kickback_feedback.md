# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The submission contains only the task description and project specifications; there is no code, script, log file, or any other artifact demonstrating that missing‑data rows are skipped, warnings are logged in the required format, or zero‑variance fields are handled. Consequently, the required error‑handling implementation and logging behavior are not evidenced.
- `T014` (rejected 1x): The repository contains a `code/visualize.py` file, but it does not include any logic that creates and saves the required scatter plot (the file ends with a stub and the plot‑generation code is absent). Moreover, the expected output file `results/power_drift_scatter.png` is not present. The task’s core requirement—producing and saving the residual‑power‑vs‑year plot with regression line and confidence intervals—is therefore unmet.
- `T016` (rejected 1x): No code, configuration, or log output files were provided showing that logging was added to the User Story 1 analysis pipeline or to the data‑filtering steps. The required artifact—a set of logging statements (e.g., using Python’s logging module) and/or a log file demonstrating recorded operation details—is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

