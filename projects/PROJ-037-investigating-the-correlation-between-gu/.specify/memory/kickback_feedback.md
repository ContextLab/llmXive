# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T026` (rejected 1x): The repository lacks the required output file `data/outputs/heatmap.png`, and the provided `code/viz.py` (as shown) contains only data‑loading utilities with no implementation of a seaborn heatmap that includes the specified title format. Consequently, the task’s core requirement—to generate and save the heatmap—is not met.
- `T027` (rejected 1x): The repository contains a partially‑implemented `code/viz.py` (truncated after a `def create_` stub) and no `data/outputs/pcoa_sleep_quality.png` file. There is no function that runs a PCoA, colors points by sleep quality, adds a legend/axis labels, and writes the required PNG, so the task’s core requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

