# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory tree under `projects/PROJ-133-investigating-the-stability-of-rotating-/` is provided; the `code`, `data`, `tests`, and `docs` subfolders (and their specified sub‑directories) are not shown to exist or contain any files. The implementer must create the full project structure as specified.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`) or scripts are present in the provided artifacts, so the claim of having configured ruff and Black cannot be verified. The required artifacts are missing.
- `T004` (rejected 1x): No evidence was provided showing that a `data/` directory (with `raw/`, `processed/`, and `aggregated/` sub‑directories) actually exists on disk; the artifact list is empty, so the required directory structure cannot be confirmed. The implementer must create the `data/` folder hierarchy and supply proof (e.g., a directory listing).
- `T017b` (rejected 1x): No updated `spec.md` file is provided, and there is no evidence that FR‑001’s grid description and the Assumptions section have been edited as required. The implementer must supply the revised specification document showing the new “256x256 grid for verification, 64x64 grid for full batch scan (conditional on RUN_FULL_GRID=true)” wording and the corresponding assumption update.
- `T017a` (rejected 1x): No updated spec.md file or excerpt showing the required performance assumptions (the 64×64 full‑scan vs 256×256 verification deviation and validation results) is provided. The evidence lacks the concrete documentation the task demands, so the requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

