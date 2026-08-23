# Contributing Guide

## Overview
This document outlines the guidelines for contributing to the PROJ-340 pipeline.

## Code Style
- **Formatting**: Use `black` for Python code formatting.
- **Linting**: Use `flake8` for linting.
- **Type Hints**: Use type hints for all function arguments and return values.
- **Documentation**: All public functions must have docstrings.

## Testing
- **Unit Tests**: Write unit tests for all new functions in `tests/unit/`.
- **Integration Tests**: Write integration tests for pipeline components in `tests/integration/`.
- **Contract Tests**: Write contract tests for data schemas in `tests/contract/`.

## Workflow
1. **Fork** the repository.
2. **Create a branch** for your feature/fix.
3. **Implement** the changes.
4. **Run tests** locally: `pytest tests/`.
5. **Submit a Pull Request**.

## Documentation
- Update `README.md` and `docs/` for any significant changes.
- Add new configuration options to `docs/execution.md`.
- Document new output artifacts in `docs/pipeline_architecture.md`.

## Data Management
- **Do not commit** large data files to the repository.
- Use `data/raw/` for local data only.
- Update `data/config/real_data_sources.yaml` for new data sources.

## Review Process
- All PRs require at least one review.
- CI checks must pass before merging.
- Ensure all new code passes the "No Fabrication" check.