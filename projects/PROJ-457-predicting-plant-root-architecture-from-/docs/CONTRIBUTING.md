# Contributing Guide

## Welcome!

Thank you for your interest in contributing to the root architecture prediction pipeline. This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.11+
- pip
- Git

### Setting Up Your Environment

1. **Fork the repository**
2. **Clone your fork**:
 ```bash
 git clone
 cd PROJ-457
 ```
3. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
4. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
5. **Install development dependencies**:
 ```bash
 pip install pytest black flake8
 ```

## Code Style

### Python Style Guide

We follow PEP 8 guidelines with the following specifics:

- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces
- **Imports**: Grouped and sorted (isort style)
- **Naming**:
 - Functions: `snake_case`
 - Classes: `PascalCase`
 - Constants: `UPPER_CASE`

### Formatting

Run Black before submitting code:

```bash
black code/
```

### Linting

Run flake8 to check for issues:

```bash
flake8 code/
```

## Testing

### Writing Tests

- **Unit tests**: `tests/unit/`
- **Contract tests**: `tests/contract/`
- **Integration tests**: `tests/integration/`

Test naming convention: `test_<function_name>_<scenario>.py`

### Running Tests

```bash
pytest tests/
```

### Test Requirements

- All new functionality must have tests
- Tests must pass before merging
- Aim for high test coverage

## Documentation

### Updating Documentation

- Update `README.md` for user-facing changes
- Update `ARCHITECTURE.md` for structural changes
- Add docstrings to new functions and classes
- Update examples in `USAGE.md`

### Docstring Format

We use Google-style docstrings:

```python
def function_name(param1, param2):
 """
 Brief description of function.

 Args:
 param1: Description of param1
 param2: Description of param2

 Returns:
 Description of return value

 Raises:
 ExceptionType: When and why this exception is raised
 """
 pass
```

## Workflow

### Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch
- Feature branches: `feature/<description>`
- Bugfix branches: `bugfix/<description>`

### Commit Messages

Follow conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build process or auxiliary tool changes

Example:
```
feat(modeling): Add R² delta calculation

Implement calculate_r2_delta function to compare LMM and RF R² scores.

Closes #123
```

### Pull Requests

1. **Create a PR** from your feature branch to `develop`
2. **Ensure all tests pass**
3. **Update documentation** as needed
4. **Request review** from maintainers
5. **Address feedback** and update PR
6. **Merge** when approved

## Data Handling

### Important Rules

- **Never fabricate data**: All data must come from real sources
- **Fail loudly**: If data fetching fails, raise an exception
- **Document exclusions**: Log all data exclusions with reasons
- **Stream large datasets**: Use streaming for datasets > 1GB

### Adding New Data Sources

1. Verify the data source is real and accessible
2. Add documentation about the source
3. Implement proper error handling
4. Add tests for the data loader
5. Update `data_ingestion.py` with new loader

## Performance Guidelines

### Resource Constraints

- **Runtime**: ≤ 6 hours
- **Memory**: ≤ 7GB RAM
- **Output size**: ≤ 100MB

### Optimization Tips

- Use streaming for large datasets
- Limit model complexity
- Profile code before optimizing
- Use appropriate data types

## Review Process

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No synthetic data or placeholders
- [ ] Error handling is appropriate
- [ ] Performance constraints are met
- [ ] Logging is adequate

### Review Turnaround

- Aiming for 24-48 hour review turnaround
- Please be patient and responsive to feedback

## Getting Help

If you need help:

1. Check existing issues and documentation
2. Ask in the project's communication channels
3. Create a new issue with detailed description

## Code of Conduct

We expect all contributors to:

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the project
- Accept constructive criticism

## License

By contributing, you agree that your contributions will be licensed under the project's license.

## Acknowledgments

Thank you to all contributors who have made this project possible!
