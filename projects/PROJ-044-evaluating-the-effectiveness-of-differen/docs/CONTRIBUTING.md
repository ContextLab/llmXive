# Contributing to PROJ-044

Thank you for your interest in contributing to the Differential Privacy in Federated Learning evaluation project. This document outlines the guidelines for contributing to the llmXive automated science pipeline.

## Code of Conduct

- Be respectful and inclusive.
- Focus on constructive feedback.
- Maintain the scientific integrity of the research.

## Development Workflow

### 1. Understanding the Task Structure

Tasks are organized in `tasks.md` and follow a specific format:
- **[ID]**: Task identifier (e.g., T029)
- **[P?]**: Parallel execution flag
- **[Story]**: User story association (US1, US2, US3)
- **Description**: Detailed task requirements

### 2. Implementing a Task

1. **Read the Task Description**: Understand the requirements and dependencies.
2. **Check Prerequisites**: Ensure all prerequisite tasks are completed.
3. **Write Tests First**: If tests are requested, write them first and ensure they fail.
4. **Implement the Code**: Write complete, executable code without placeholders.
5. **Verify Real Data**: Ensure all data loaders use real sources and fail loudly if unavailable.
6. **Run Tests**: Ensure all tests pass.
7. **Update Documentation**: If applicable, update relevant docs.

### 3. Code Standards

- **Python**: Follow PEP 8 guidelines. Use `black` for formatting and `ruff` for linting.
- **Imports**: Only import names that exist in the provided API surface. Do not invent new names.
- **Comments**: Add docstrings for all functions and classes.
- **Error Handling**: Fail loudly; never suppress errors or use synthetic fallbacks.

### 4. Data Integrity

- **No Synthetic Data**: All data must come from real, programmatically accessible sources.
- **Checksums**: Generate and verify SHA256 checksums for all downloaded data.
- **Reproducibility**: Use fixed seeds for all random operations.

### 5. Testing Guidelines

- **Unit Tests**: Test individual functions and modules.
- **Integration Tests**: Test interactions between components.
- **Reproducibility Tests**: Ensure identical results with the same seed.
- **Edge Cases**: Test for empty datasets, timeout triggers, and zero-sample clients.

### 6. Documentation

- **README.md**: Update with new features or changes.
- **docs/**: Add or update documentation files as needed.
- **Code Comments**: Keep inline comments clear and concise.

## Submitting Changes

1. **Fork the Repository**: Create a personal copy of the project.
2. **Create a Branch**: Use a descriptive branch name (e.g., `feature/T029-docs`).
3. **Commit Changes**: Write clear commit messages.
4. **Submit a Pull Request**: Describe the changes and reference the task ID.

## Review Process

- **Automated Checks**: Code must pass linting and formatting checks.
- **Manual Review**: A maintainer will review the code for correctness and adherence to guidelines.
- **Testing**: All tests must pass before merging.

## Common Pitfalls

- **Placeholder Code**: Do not submit `pass`, `TODO`, or `NotImplementedError`.
- **Synthetic Data**: Do not fabricate data or use mock datasets.
- **Invented APIs**: Do not import names that do not exist in the provided API surface.
- **Ignoring Dependencies**: Ensure all prerequisite tasks are completed before starting a new task.

## Questions?

If you have questions or need clarification, please open an issue or contact the maintainers.
