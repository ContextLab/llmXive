# Tests Directory

This directory contains the test suite for the llmXive Follow-up project.

## Structure

- `contract/`: Tests verifying data schemas and API contracts (e.g., JSON schema validation).
- `integration/`: Tests verifying end-to-end workflows and component interactions.
- `unit/`: Tests verifying individual functions and classes in isolation.

## Running Tests

Run the full suite:
```bash
pytest tests/
```

Run specific categories:
```bash
pytest tests/contract/
pytest tests/integration/
pytest tests/unit/
```
