# Contract Schemas

This directory contains Pydantic-based schema validators for the llmXive pipeline data artifacts.

## Modules

- `dataset_schema.py`: Validates `VideoClip` and `Dataset` records.
- `metric_schema.py`: Validates `MetricRecord` and `MetricSchema` records.
- `analysis_schema.py`: Validates `AnalysisResult` and `AnalysisSchema` records.

## Usage

Each module provides a `Validator` class with static methods:
- `validate_json(json_str)`: Validates a JSON string.
- `validate_file(file_path)`: Validates a JSON file.
- `validate_sample()`: Demonstrates validation with a sample record.
- `test_invalid_record()`: Demonstrates error handling with an invalid record.

## Running Tests

To verify schema validation logic:
```bash
python -m pytest tests/contract/test_schema_validators.py -v
```

Or run the `__main__` block in each schema file:
```bash
python code/contracts/dataset_schema.py
python code/contracts/metric_schema.py
python code/contracts/analysis_schema.py
```