# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required `projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/` directory (or any of its sub‑folders/files) is provided; the implementer only supplied a textual description without the actual project structure. The task therefore remains unfulfilled.
- `T002b` (rejected 1x): The claim only references a placeholder token ({{claim:c_bed10a97}}) and provides no actual logs, version outputs, or checksum file showing that R, Seurat v4, and reticulate were installed. Evidence of `R --version`, `Rscript -e "packageVersion('Seurat')"` results, or a recorded package‑list checksum is missing, so the task is not verified as completed.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with `[tool.black]`, `ruff.toml`, or a `.pre-commit-config.yaml` invoking ruff/black) are present in the `projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/` directory, nor any evidence of these tools being set up. The required artifacts are missing, so the task is not satisfied.
- `T004` (rejected 1x): The implementer did not provide any evidence (e.g., a file tree, screenshots, or listings) showing that the required `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, and `tests/integration/` directories have been created. Without such artifacts, we cannot confirm the directory structure exists. The missing directory hierarchy must be added and documented.
- `T004a` (rejected 1x): No artifact (e.g., conda install log, `~/.ncbi/settings` file, or output of `prefetch --help`) was provided to demonstrate that the SRA Toolkit was installed, configured, and verified as required. The claim lacks any concrete evidence of completion.
- `T005` (rejected 1x): No `download_data.py` script is present, and the required raw count matrix files are not found in `data/raw/`. Without these artifacts, the task of fetching the specified GEO datasets via the SRA Toolkit has not been demonstrated.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

