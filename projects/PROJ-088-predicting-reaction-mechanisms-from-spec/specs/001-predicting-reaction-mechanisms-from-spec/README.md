# Contract Definitions

This directory contains the formal schema definitions for data interchange within the `llmXive` pipeline for Project PROJ-088.

## Files

- `dataset.schema.yaml`: Defines the structure of the preprocessed spectroscopic dataset.
 - Enforces 512-bin spectrum length.
 - Restricts labels to valid reaction mechanisms (SN1, SN2, E1).
 - Restricts provenance to `kinetic_studies` or `validated_intermediates` (FR-008).

- `output.schema.yaml`: Defines the structure of model training reports and feature importance analysis.
 - Includes cross-validation metrics (accuracy, F1).
 - Includes stability variance and BH-corrected significance.
 - Explicitly avoids causal language in descriptions (FR-006).

## Usage

These YAML files serve as the source of truth for data validation.
The `tests/contract/test_schema_validation.py` file contains unit tests that verify:
1. The YAML files are syntactically valid.
2. The required fields are present.
3. The constraints (enums, min/max) are correctly defined.

## Versioning

- `dataset.schema.yaml`: v1.0.0
- `output.schema.yaml`: v1.0.0