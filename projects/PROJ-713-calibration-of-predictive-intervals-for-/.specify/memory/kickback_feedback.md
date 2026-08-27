# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listing or file manifest for `projects/PROJ-713-calibration-of-predictive-intervals-for-/code/` was provided, so we cannot confirm that the required folder structure actually exists. The implementer must supply evidence (e.g., a tree view or list of files) showing the created directory.
- `T001b` (rejected 1x): No evidence was provided that the `projects/PROJ-713-calibration-of-predictive-intervals-for-/tests/` directory actually exists (or contains any files). Without a visible artifact, the requirement cannot be confirmed as satisfied.
- `T001c` (rejected 1x): No evidence of the required `data/raw/` and `data/processed/` directories is provided; the claim lacks any artifact (e.g., a directory listing, creation script output, or screenshot) confirming their existence. The implementer must supply concrete proof that these directories have been created and are non‑empty.
- `T001d` (rejected 1x): No `results/` directory (or any listing of its contents) is provided in the evidence, and the implementer did not include any artifact showing that the required directory structure was created. The task remains undone.
- `T003` (rejected 1x): The provided artifacts relate only to the predictive‑interval calibration feature; there are no flake8 or black configuration files, no linting setup scripts, and no evidence that linting/formatting tools have been added to the project. Consequently the requirement to configure linting and formatting is unmet.
- `T009` (rejected 1x): No `data/raw/` or `data/processed/` directories, nor any script/module implementing checksum verification, are present in the provided artifacts. The claim lacks concrete evidence of the required directory structure and verification logic, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

