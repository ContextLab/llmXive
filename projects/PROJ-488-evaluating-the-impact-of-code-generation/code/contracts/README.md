# Contracts Module Documentation

This directory contains the formal contracts for the `PROJ-488-evaluating-the-impact-of-code-generation` pipeline.

## Overview

Contracts ensure that data, APIs, and validation logic remain consistent and correct throughout the pipeline execution.

## Structure

- `data_contracts.py`: Defines schemas and validators for data models (CodeSnippet, MetricScore, etc.).
- `api_contracts.py`: Defines the expected CLI interface and function signatures.
- `validation_contracts.py`: Implements pre-condition and post-condition checks for pipeline stages.
- `__init__.py`: Exports public contract interfaces.
- `README.md`: This file.

## Usage

Import contracts in pipeline stages to enforce rules:

```python
from code.contracts import validate_preconditions, validate_postconditions, CodeSnippetContract

def my_stage(config):
 validate_preconditions("my_stage", config)
 #... logic...
 validate_postconditions("my_stage", config, result)
```

## Data Models

All data contracts align with the definitions in `code/data_model.py`:
- `CodeSnippet`
- `MetricScore`
- `DatasetGroup`
- `MetricResult`

## Validation Rules

- **Pre-conditions**: Check existence of input files, directory permissions, and required config keys.
- **Post-conditions**: Verify output file creation, non-empty content, and schema compliance.

## Error Handling

Violations raise `ContractViolationError`, which should be caught and logged by the main pipeline controller.