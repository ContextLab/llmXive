# Schema Definition & Validation

This document provides a concise overview of the data schemas used throughout the
*Quantifying the Complexity of Knot Diagrams* project and describes how to validate
datasets against these schemas.

## Schema catalogue

All schema definitions are stored under the `specs/` directory. The most relevant
schemas are:

* `specs/010-quantifying-the-complexity-of-knot-diagr/contracts/dataset.schema.yaml`
  – defines the top‑level structure of processed datasets.
* `specs/010-quantifying-the-complexity-of-knot-diagr/contracts/knot_record.schema.yaml`
  – describes a single knot record, including its invariants and metadata.
* `specs/010-quantifying-the-complexity-of-knot-diagr/contracts/regression-model.schema.yaml`
  – specifies the required fields for regression model specifications.

Each schema follows the **YAML** format and is compatible with the **jsonschema**
library.

## Validation workflow

The project ships a lightweight validator located at `code/data/validator.py`.
It provides a single public function:

```python
from code.data.validator import validate_against_schema

# Example: validate a processed dataset
validate_against_schema(
    data_path="data/processed/knots_validated.csv",
    schema_path="specs/010-quantifying-the-complexity-of-knot-diagr/contracts/dataset.schema.yaml",
)
```

The function raises a `jsonschema.ValidationError` if the data does not conform to
the schema, otherwise it returns `True`.

### Command‑line usage

For quick checks you can run the validator as a module:

```bash
python -m code.data.validator \
    --data data/processed/knots_validated.csv \
    --schema specs/010-quantifying-the-complexity-of-knot-diagr/contracts/dataset.schema.yaml
```

The exit code will be `0` on success and non‑zero on validation failure.

## Adding or updating schemas

When a new data artefact is introduced, follow these steps:

1. **Create** a new schema file under the appropriate `specs/…/contracts/` folder.
2. **Reference** the schema in the documentation (this file) and, if needed, add a
   corresponding test in `tests/contract/`.
3. **Run** the validator on existing data to ensure backward compatibility.

Keeping schemas up‑to‑date guarantees reproducibility and facilitates downstream
analysis.

