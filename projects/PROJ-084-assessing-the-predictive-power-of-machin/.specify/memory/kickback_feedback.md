# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (`code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`) being present on disk is provided; the claim is unsubstantiated. The implementer must create these folders (e.g., via `mkdir -p`) and show that they exist and are non‑empty.
- `T007a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007b` (rejected 1x): The repository lacks the required `dataset.schema.yaml` file, and `code/utils/validators.py` is truncated (e.g., `OutputSchema` definition is incomplete and functions like `load_schema`, `validate_dataset_file` are not present). Consequently the module cannot actually load a schema or validate rows as the task demands.
- `T008a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008b` (rejected 1x): The provided `code/utils/validators.py` is truncated (e.g., `OutputSchema` definition ends abruptly and no `load_schema` or output‑validation functions are present). Moreover, the required `output.schema.yaml` file is missing from the repository. Consequently the module does not actually load or enforce the output schema as the task demands.
- `T014` (rejected 1x): The repository lacks the required input files (`data/raw/uspto_raw.parquet` and `data/results/download_checksum.txt`), and the provided `sanitize.py` does not actually load the parquet, verify the checksum against the file, or write out sanitized SMILES as the task specifies. Consequently the core functionality and prerequisite data are missing.
- `T017` (rejected 1x): The repository contains `code/preprocessing/ingest.py`, but the required output file `data/processed/cleaned_reactions.parquet` is not present, and the referenced schema file `specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml` is also missing. Without these artifacts the pipeline cannot be validated against the schema nor produce the cleaned dataset, so the task is not fully satisfied.
- `T018` (rejected 1x): The repository contains `code/preprocessing/ingest.py`, but the shown code is truncated and does not demonstrate logging of exclusion reasons, calculation of `exclusion_fraction`, or writing of `data/results/data_quality_report.json`. Moreover, the required `data_quality_report.json` file is absent from the project. These missing pieces mean the task’s requirements are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

