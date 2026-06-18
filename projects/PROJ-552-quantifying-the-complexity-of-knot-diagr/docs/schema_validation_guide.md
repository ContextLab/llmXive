# Schema Definition & Validation Guide

This document provides an overview of the JSON schema definitions used in the
project and how they are validated programmatically.

## Schemas

The project stores its schema definitions in the `specs/010-quantifying-the-
complexity-of-knot-diagr/contracts/` directory. Key schemas include:

* `dataset.schema.yaml` – describes the top‑level dataset metadata.
* `knot-record.schema.yaml` – defines the required fields for each knot
  record.
* `regression-model.schema.yaml` – specifies the format for regression model
  specifications.

## Validation utilities

The module `code/data/validator.py` provides a helper function
`validate_json_schema(data: dict, schema_path: str) -> None` that raises a
`jsonschema.exceptions.ValidationError` if the supplied data does not conform
to the given schema. Example usage:

```python
from code.data.validator import validate_json_schema

# Load your data as a dict/list, e.g., using json.load or pandas
data = ...
validate_json_schema(data, "specs/010-quantifying-the-complexity-of-
knot-diagr/contracts/dataset.schema.yaml")
```

All validation steps are integrated into the reproducibility pipeline and are
executed as part of the `quickstart_validator` entry point.

