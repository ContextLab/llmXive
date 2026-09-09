# Contributing to the Halo Shape Analysis Pipeline

Thank you for your interest in contributing! This document outlines the guidelines for development.

## Development Workflow
1. **Fork and Clone**: Create a fork of the repository and clone it locally.
2. **Environment**: Ensure you are using Python 3.11+ and have installed dependencies via `pip install -r requirements.txt`.
3. **Branching**: Create a new branch for your feature or bug fix (e.g., `feature/new-stat-test`).
4. **Coding Standards**:
 - Format code with `black`.
 - Lint code with `ruff`.
 - Follow the existing module structure (`ingestion`, `processing`, `analysis`).
5. **Testing**:
 - Write unit tests for new logic in `code/tests/`.
 - Ensure all tests pass: `pytest code/tests/`.
6. **Documentation**: Update `README.md` or `docs/` if you change behavior or add features.
7. **Pull Request**: Submit a PR with a clear description of changes.

## Code Style
- **Formatting**: Use `black` (line length 100).
- **Imports**: Use absolute imports (e.g., `from utils.config import...`).
- **Comments**: Docstrings are required for all public functions.

## Data Handling
- **Real Data Only**: Do not commit synthetic data or placeholder CSVs.
- **Large Files**: Do not commit HDF5 files or large datasets to Git. Use `.gitignore`.
- **API Keys**: Never commit API keys. Use environment variables.

## Reporting Issues
If you encounter bugs or have suggestions, please open an issue with:
- A clear description of the problem.
- Steps to reproduce.
- Environment details (OS, Python version).
