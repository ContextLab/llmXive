# Contributing to PROJ-340

Thank you for your interest in contributing to the Gut Microbiome-Sleep Correlation Pipeline.

## Code of Conduct

- **No Fabrication**: Never generate synthetic data to replace real measurements in final outputs.
- **Reproducibility**: All code must be deterministic (use fixed seeds) and well-documented.
- **Rigor**: Statistical methods must be appropriate for the data type.

## How to Contribute

### 1. Reporting Issues

- Use the GitHub Issue tracker.
- Provide a clear description of the problem.
- Include steps to reproduce.

### 2. Submitting Changes

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/my-feature`).
3. Make your changes.
4. Write tests.
5. Ensure all tests pass.
6. Submit a pull request.

### 3. Testing

- **Unit Tests**: Run `pytest tests/unit/`.
- **Integration Tests**: Run `pytest tests/integration/`.
- **Pipeline Test**: Run `python code/main.py --mode synthetic`.

### 4. Documentation

- Update `README.md` and `docs/` if you add new features.
- Add docstrings to all functions.

## Development Setup

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 pip install pytest pytest-cov
 ```
3. Run tests:
 ```bash
 pytest
 ```

## Style Guide

- **Python**: Follow PEP 8.
- **Formatting**: Use `black` and `flake8`.
- **Imports**: Sort imports with `isort`.

## Review Process

- All PRs must be reviewed by at least one maintainer.
- CI checks must pass.
- No synthetic data in final reports.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
