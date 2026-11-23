# Contributing to llmXive Drift Detection

Thank you for your interest in contributing! This document outlines the guidelines for contributing to this project.

## Code of Conduct

Please be respectful and constructive in all interactions.

## Getting Started

1. **Fork the repository**.
2. **Clone your fork**:
 ```bash
 git clone
 cd projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5
 ```
3. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate
 ```
4. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Development Workflow

1. **Create a branch** for your feature or bugfix:
 ```bash
 git checkout -b feature/your-feature-name
 ```
2. **Make your changes**.
3. **Run tests**:
 ```bash
 pytest tests/
 ```
4. **Format and lint your code**:
 ```bash
 black code/
 ruff check code/
 ```
5. **Commit your changes**:
 ```bash
 git commit -m "Add feature: your feature description"
 ```
6. **Push to your fork** and submit a **Pull Request**.

## Coding Standards

- **Language**: Python 3.11+
- **Style**: Follow PEP 8 guidelines. Use `black` for formatting.
- **Type Hinting**: Use type hints for all function arguments and return values.
- **Documentation**: Add docstrings to all public functions and classes.
- **Testing**: Write unit tests for new functionality.

## Pull Request Process

1. Ensure all tests pass.
2. Update documentation if necessary.
3. Ensure your code passes `ruff` linting and `black` formatting.
4. Provide a clear description of your changes in the PR.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub with:
- A clear title and description.
- Steps to reproduce the issue (if applicable).
- Expected vs. actual behavior.

## License

By contributing, you agree that your contributions will be licensed under the project's license.
