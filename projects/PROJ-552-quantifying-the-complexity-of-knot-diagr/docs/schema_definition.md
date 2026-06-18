# Schema Definition

The schemas are defined in the `specs/` directory as YAML files adhering to the JSON Schema draft‑07 specification. Validation is performed using the `jsonschema` Python library, ensuring that all data artifacts conform to the expected structure before downstream analysis. & Validation

The project defines its data contracts using JSON Schema files located in the `specs/` directory. Key schemas include:

- `dataset.schema.yaml` – describes the structure of dataset metadata.
- `knot-record.schema.yaml` – defines the required fields for each knot record.
- `regression_model.schema.yaml` – specifies the inputs and outputs of regression models.

Validation is performed by the `code/data/validator.py` module, which loads the appropriate schema and checks JSON payloads using the `jsonschema` library. Validation errors are reported with clear messages indicating the offending field and the expected type or constraint.

To validate a JSON file from the command line:

```bash
python -m code.data.validator path/to/file.json --schema specs/010-quantifying-the-complexity-of-knot-diagr/contracts/knot-record.schema.yaml
```

The validator is also integrated into the reproducibility pipeline; any schema violations cause the pipeline to abort and log the issue in `docs/reproducibility/validation_status.md`.

For more details, see the existing `docs/schema_validation_guide.md` and the schema files themselves.

