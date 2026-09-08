# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings or file system evidence were provided showing that the required `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/...` folders exist; without such proof the task requirement is not satisfied.
- `T001b` (rejected 1x): The required files under `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/` (`code/requirements.txt`, `.gitignore`, and `pytest.ini`) are missing; only a unrelated `code/requirements.txt` exists elsewhere. The task to create those empty project files is therefore not satisfied.
- `T001c` (rejected 1x): The required file `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/requirements.txt` does not exist, so the task of writing a pinned‑version requirements file at the specified location is not fulfilled. The existing `code/requirements.txt` is at a different path and does not satisfy the path requirement.
- `T001d` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T001f` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/features.json, schema.yaml
- `T001e` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/features.json, results/results.json
- `T003a` (rejected 1x): The `pyproject.toml` file is present and correctly pins `ruff==0.9.0` and `black==24.8.0`, but the required `.ruff.toml` file is missing entirely, so the task’s requirement of creating both configuration files is not satisfied.
- `T037c` (rejected 1x): No code, data files, or generated outputs were provided; the claim contains only a textual description of desired functionality without any actual ingestion script, feature‑engineering module, or predictive‑model artifacts. Consequently the required synthetic dataset generation and associated processing steps are not demonstrated.
- `T014` (rejected 1x): No code, scripts, data files, or output artifacts (e.g., dataset ingestion script, entanglement feature‑engineering module, or Random Forest training/validation results) were provided for inspection, so the required deliverables cannot be confirmed as existing or correct. The implementer must supply the actual implementation files and evidence of their execution.
- `T022a` (rejected 1x): No code, data files, or output artifacts (e.g., dataset ingestion script, per‑sample entanglement JSON, covariance matrix/eigenvalue results, or predictive model training script) are present to verify that the required functionality was implemented. The claim cannot be confirmed without these concrete artifacts.
- `T022c` (rejected 1x): No code, data files, or output artifacts (e.g., dataset ingestion script, JSON feature records, Mahalanobis distance calculations, or model training results) were provided. The required implementations for loading the Z‑Reward dataset, computing per‑sample entanglement metrics, and producing the conditional Mahalanobis distance outputs are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

