# Contributing to llmXive

Thank you for your interest in contributing! This document outlines the guidelines for adding new features, datasets, or models.

## Development Setup

1. **Fork and Clone**
 ```bash
 git clone <your-fork>
 cd <project-root>
 pip install -r requirements.txt
 ```

2. **Environment**
 - Ensure you are working in a CPU-only environment.
 - Set up a virtual environment if desired.

## Adding a New Dataset

1. **Verify Source**: Ensure the dataset is from a verified, real source (e.g., Hugging Face, official repo).
2. **Implement Downloader**: Create `src/data/download_<name>.py` following the pattern of existing downloaders.
3. **Update Schema**: If the dataset has unique fields, update `contracts/dataset.schema.yaml`.
4. **Add Task**: Define a new task in `tasks.md` with Impl and Exec phases.
5. **Test**: Write unit tests in `tests/unit/test_download_<name>.py`.

## Adding a New Model

1. **Update Candidate List**: Add the model to `src/utils/config.py`.
2. **Implement Loader**: Ensure the model can be loaded in low-bit CPU mode.
3. **Update Prompting**: Modify `src/models/llm_inference.py` if the model requires specific prompting.
4. **Benchmark**: Run the model selection script to verify performance.

## Code Style

- **Formatting**: Use `black` for code formatting.
- **Linting**: Use `ruff` for linting.
- **Type Hints**: All functions must have type hints.
- **Docstrings**: Use Google-style docstrings for all public functions.

## Testing

- **Unit Tests**: All new code must have corresponding unit tests.
- **Integration Tests**: Run the full pipeline on a small sample to verify integration.
- **CI/CD**: Ensure all tests pass before submitting a PR.

## Reporting Issues

- **Bug Reports**: Include error logs, stack traces, and steps to reproduce.
- **Feature Requests**: Describe the use case and expected behavior.

## License

By contributing, you agree that your contributions will be licensed under the project's license.
