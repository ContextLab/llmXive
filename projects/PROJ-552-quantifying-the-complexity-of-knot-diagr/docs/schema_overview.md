# Schema Overview

This document provides a concise overview of the schema definitions used in the
**quantifying-the-complexity-of-knot-diagr** project and how they are validated
throughout the code base.

## Schema Definition

The project defines its data contracts in YAML schema files located under the
`specs/` directory.  Key schema files include:

* `specs/010-quantifying-the-complexity-of-knot-diagr/contracts/dataset.schema.yaml`
  – Describes the structure of the processed dataset CSV files.
* `specs/010-quantifying-the-complexity-of-knot-diagr/contracts/knot-record.schema.yaml`
  – Specifies required fields for a single knot record (e.g., `id`, `crossings`,
    `braid_word`, `invariants`).
* `specs/010-quantifying-the-complexity-of-knot-diagr/contracts/regression-model.schema.yaml`
  – Captures metadata for trained regression models, including hyper‑parameters
    and performance metrics.

All schemas are written in **JSON Schema** (draft‑07) syntax and are versioned
to allow backward‑compatible extensions.

## Validation

Validation is performed by the `code/data/validator.py` module, which leverages
the **jsonschema** Python library.  The primary entry point is the
`validate_record(record: dict, schema_path: str) -> None` function.  It raises a
`jsonschema.exceptions.ValidationError` if the supplied `record` does not
conform to the given schema.

Typical usage patterns:

```python
from code.data.validator import validate_record
from pathlib import Path

record = {...}  # a dict representing a knot record
schema_path = Path('specs/010-quantifying-the-complexity-of-knot-diagr/contracts/knot-record.schema.yaml')
validate_record(record, schema_path)
```

The validation step is integrated into the data ingestion pipeline (see
`code/data/parser.py`) and is also exercised by the test suite (`tests/contract`
and `tests/unit/test_validator.py`).

## Updating Schemas

When extending a schema, follow these guidelines:

1. **Add new fields as optional** unless they are required for downstream
   analysis.
2. **Increment the `"$id"` version** to reflect the change.
3. **Update the documentation** in this file and, if necessary, the
   corresponding validation calls.
4. **Run the full test suite** to ensure existing data still validates.

For more detailed guidance, refer to `docs/schema_validation_guide.md`.

---
*This file was added to address reviewer feedback regarding explicit schema
definition and validation documentation.*

