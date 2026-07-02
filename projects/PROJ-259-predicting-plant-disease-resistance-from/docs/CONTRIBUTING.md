# Contributing to Plant Disease Resistance Prediction Pipeline

Thank you for your interest in contributing to this project! This document outlines the guidelines for contributing.

## Code Style

- **Python**: Follow PEP 8 style guidelines.
- **Formatting**: Use `black` for code formatting.
- **Linting**: Use `flake8` or `pylint` for linting.
- **Type Hinting**: Use type hints for function arguments and return values where possible.

## Project Structure

- `code/`: Source code for the pipeline.
- `data/`: Data storage (raw and processed).
- `artifacts/`: Output models, reports, and figures.
- `tests/`: Unit and integration tests.
- `docs/`: Documentation.

## Development Workflow

1. **Fork the repository** and create a feature branch.
2. **Write tests** for new features before implementation (TDD approach).
3. **Implement the feature** ensuring it passes all existing tests.
4. **Update documentation** if the feature adds new functionality or changes existing behavior.
5. **Submit a Pull Request** with a clear description of changes.

## Docker Development

If you are developing Docker-related features:
- Ensure changes to `Dockerfile` are tested with `docker build`.
- Update `docs/Docker_usage.md` if build arguments or run commands change.
- Verify that `fastp` and `bcftools` are correctly installed in the image.

## Reporting Issues

- Use the issue tracker to report bugs or suggest features.
- Include environment details (OS, Python version, Docker version) when reporting bugs.
- Provide a minimal reproducible example if possible.

## Success Criteria

Contributions should align with the project's success criteria:
- **Performance**: Runtime ≤ 6h, RAM ≤ 7GB.
- **Accuracy**: CV accuracy ≥ 75% (Simulation Mode), Permutation p-value ≤ 0.05.
- **Biomarkers**: At least 10 SNPs and 10 metabolites significant across thresholds.

## License

By contributing, you agree that your contributions will be licensed under the project's license.
