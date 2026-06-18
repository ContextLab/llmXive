# Schema Conformance Summary

All datasets and records produced by this project are validated against the JSON Schema definitions located in `specs/010-quantifying-the-complexity-of-knot-diagr/contracts/`. Validation is performed automatically during the data processing pipeline using the `code/data/validator.py` module. The validation results are logged in `data/processed/validation_flags.json` and any non‑conforming entries are reported in the reproducibility logs.

The following schemas are used:

- `dataset.schema.yaml` – describes the overall dataset structure.
- `knot-record.schema.yaml` – describes individual knot records.
- `regression-model.schema.yaml` – describes regression model metadata.

All current releases pass validation with zero errors.
