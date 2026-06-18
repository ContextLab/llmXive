# Schema Conformance

All schemas in `specs/010-quantifying-the-complexity-of-knot-diagr/contracts/` have been validated against JSON Schema Draft-07 using the `jsonschema` Python library. The repository includes both hyphenated (`knot-record.schema.yaml`) and underscored (`knot_record.schema.yaml`) filenames for backward compatibility.

This project defines its data contracts in the **specs/010-quantifying-the-complexity-of-knot-diagr/contracts** directory.

* `dataset.schema.yaml` – describes the top‑level dataset structure.
* `knot-record.schema.yaml` – defines the required fields for each knot record.
* `regression-model.schema.yaml` – specifies the format of regression model metadata.

All data files produced by the pipeline are validated against these schemas by the
`code/data/validator.py` module.  Validation is performed automatically during
the reproducibility checks (`code/reproducibility/quickstart_validator.py`) and
fails fast if any record does not conform.  Keeping the schemas up‑to‑date and
ensuring that new pipeline stages respect them is essential for reproducibility
and downstream analysis.

If you add new fields to any data artifact, remember to:

1. Update the corresponding schema file.
2. Extend the validation logic in `code/data/validator.py` if custom checks are required.
3. Add tests in `tests/contract/test_schemas.py` to cover the new schema rules.

The CI pipeline includes a step that runs the validator on the processed data
and will reject any pull request that introduces schema violations.

