## Schema Definition & Validation

The project defines all data contracts using **YAML schema files** located under the
`specs/` directory (e.g., `specs/010-quantifying-the-complexity-of-knot-diagr/contracts/`).
Each schema follows the **JSON Schema** specification and describes the required
fields, data types, and constraints for datasets, knot records, and regression
models.

Validation of these schemas is performed by the **`code/data/validator.py`** module.
It provides a `validate(instance_path, schema_path)` function that loads the
appropriate YAML schema and checks a given JSON/YAML instance, raising a
`ValidationError` with detailed messages when the data does not conform.  The
validation step is integrated into the data ingestion pipeline and is also
exercised by the test suite (`tests/contract/test_schemas.py`).

To validate a file manually, run:

```bash
python -m code.data.validator path/to/data.json specs/.../your_schema.schema.yaml
```

This ensures that all generated artifacts adhere to the agreed‑upon contracts
before downstream analysis.

