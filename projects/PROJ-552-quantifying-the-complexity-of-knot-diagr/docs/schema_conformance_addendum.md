# Schema Conformance

All data artifacts produced by this project are validated against the JSON schemas defined in `specs/010-quantifying-the-complexity-of-knot-diagr/contracts/`. The primary schemas are:

- `dataset.schema.yaml`
- `knot-record.schema.yaml`
- `regression-model.schema.yaml`

The validation is performed by `code/data/validator.py` and integration tests in `tests/contract/test_schemas.py`. Any deviation will cause the pipeline to abort.

