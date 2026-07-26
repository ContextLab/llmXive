# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): No search results, data files, or documentation were provided showing that Metabolomics Workbench was queried for terpenoid, alkaloid, or phenylpropanoid defense‑metabolite experiments. The required artifact—a list or CSV of relevant experiment IDs (with metadata) – is missing.
- `T014` (rejected 1x): No artifact (e.g., a CSV, JSON log, or summary report) showing the result of the metadata comparison and the ≥95 % sample‑level match rate is present; the implementer supplied only the task description and specifications without any concrete output. The required evidence of pairing feasibility is missing.
- `T016` (rejected 1x): The required file `projects/PROJ-503-predicting-plant-defense-compound-produc/data/sources.yaml` does not exist; only a `data/sources.yaml` at a different location is present, so the task’s specified artifact is missing.
- `T017` (rejected 1x): No `research.md` file containing dataset citations and availability status for Phase 0 was found in the provided artifacts; thus the required document is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

