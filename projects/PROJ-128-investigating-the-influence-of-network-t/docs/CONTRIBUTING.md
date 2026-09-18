# Contributing to PROJ-128

Thank you for your interest in contributing to this research project! This document outlines the guidelines for contributing.

## Code of Conduct

- Be respectful and constructive in all interactions.
- Focus on scientific rigor and reproducibility.
- Avoid scope creep; adhere strictly to FR-001 through FR-008.

## How to Contribute

### Reporting Issues

- Use the issue tracker to report bugs or suggest features.
- Provide clear reproduction steps for bugs.
- Link to relevant documentation or literature for feature requests.

### Submitting Changes

1. Fork the repository.
2. Create a feature branch from `main`.
3. Implement your changes with tests.
4. Ensure all existing tests pass.
5. Submit a pull request.

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines.
- Use `black` for formatting and `flake8` for linting.
- Type hints are encouraged.

### Testing

- Write unit tests for new functionality.
- Ensure integration tests pass before merging.
- Avoid synthetic data; use real HCP data for validation.

### Documentation

- Update `README.md` and `docs/` for significant changes.
- Include docstrings for all public functions.
- Document configuration parameters in `config.py`.

### Data Integrity

- **Never fabricate data**: All metrics must come from real HCP data.
- **Fail loudly**: If data loading fails, raise an error rather than falling back to synthetic data.
- **Reproducibility**: Ensure scripts produce consistent results with fixed seeds.

### Scope Adherence

- Only implement features explicitly mandated by FR-001 through FR-008.
- Do not add unapproved sensitivity analyses (e.g., tractography confidence).
- Maintain "associational" framing in all reports.

## Review Process

- All pull requests require at least one reviewer approval.
- CI/CD checks must pass (tests, linting, validation).
- Documentation updates are required for significant changes.

## Questions?

Open an issue for any questions or clarifications.