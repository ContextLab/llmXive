# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The implementer did not provide any evidence that the required directories (`code/`, `tests/`, `data/`, `results/`) actually exist or contain any files; only narrative user stories were shown. The project structure itself is missing, so the task is not satisfied.
- **T002a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T002b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T002c** — The provided `code/utils/schema_validator.py` is present but the required schema file `contracts/dataset.schema.yaml` does not exist, so the loader cannot succeed. Moreover, the script does not show a complete implementation for reading BIDS `events.tsv` files, handling TSV/JSON parsing errors, or exiting with the specified error codes. These essential parts are missing.
- **T010b** — No evidence of a downloaded OpenNeuro metadata file (or any files) in `data/raw/openneuro/` is provided, nor any logs showing error handling or continuation to the next pipeline step. The required artifact is missing, so the task is not satisfied.
- **T011b** — The `code/02_audit_metadata.py` script contains validation logic that imports and calls `utils.schema_validator`, but the required schema file `contracts/dataset.schema.yaml` is missing, so the validation cannot actually be performed. The missing schema file must be added (or the path corrected) for the implementation to be functional.
