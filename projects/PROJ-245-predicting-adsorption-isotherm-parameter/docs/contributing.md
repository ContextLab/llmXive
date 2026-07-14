# Contributing Guide

## Development Workflow

1. **Fork & Clone**:
 ```bash
 git clone <your-fork-url>
 cd PROJ-245-predicting-adsorption-isotherm-parameter
 ```

2. **Environment Setup**:
 ```bash
 python -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 ```

3. **Branching**:
 Create a new branch for your feature or bugfix.
 ```bash
 git checkout -b feature/your-feature-name
 ```

4. **Coding Standards**:
 - Use `black` for formatting and `ruff` for linting.
 - Write type hints for all function arguments and return values.
 - Ensure all new code has corresponding unit tests in `tests/unit/`.

5. **Testing**:
 Run the test suite before committing.
 ```bash
 pytest tests/ -v
 ```

6. **Commit Messages**:
 Use the conventional commits format:
 - `feat: Add new feature`
 - `fix: Fix bug`
 - `docs: Update documentation`
 - `refactor: Refactor code`

7. **Pull Request**:
 - Push your branch and open a Pull Request (PR) against the `main` branch.
 - Ensure all CI checks (linting, tests) pass.
 - Provide a clear description of the changes and link to relevant issues.

## Project Structure Guidelines

- **Code**: All source code must reside in `code/`.
- **Data**: Do not commit large data files. Use `.gitignore` for `data/raw/` and `data/processed/`. Only commit small sample data or scripts that generate data.
- **Tests**: Place unit tests in `tests/unit/` and integration tests in `tests/integration/`.
- **Documentation**: Update `docs/` whenever you change the API or workflow.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub. Include:
- A clear description of the issue.
- Steps to reproduce (if applicable).
- Expected vs. actual behavior.
- Environment details (Python version, OS).

## Code Review

All PRs require at least one approval. Reviewers will check:
- Code quality and adherence to standards.
- Test coverage.
- Documentation updates.
- Correctness of the implementation relative to the task description.
