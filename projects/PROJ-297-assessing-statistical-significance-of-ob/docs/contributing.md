# Contributing Guide

## Welcome!

Thank you for your interest in contributing to the Statistical Significance Assessment Pipeline. This guide will help you get started.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the project

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone
cd PROJ-297-assessing-statistical-significance-of-ob
```

### 2. Setup Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies and dev tools
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 isort
```

### 3. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name
```

## Development Workflow

### 1. Understand the Task

- Check `tasks.md` for current tasks
- Read the relevant user story in `spec.md`
- Understand dependencies and prerequisites

### 2. Write Tests First

For new features:
1. Write failing tests in `tests/`
2. Run tests to confirm they fail
3. Implement the feature
4. Run tests to confirm they pass

### 3. Implement the Feature

- Follow existing code style
- Add type hints to all functions
- Write clear docstrings
- Keep functions focused and single-purpose

### 4. Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=code --cov-report=html

# Run specific test file
python -m pytest tests/unit/test_stats_engine.py -v
```

### 5. Format and Lint

```bash
# Format code
black code/
isort code/

# Run linter
flake8 code/
```

### 6. Verify Pipeline Execution

```bash
# Run a quick validation
python code/main.py --task synthetic_validation

# Run full pipeline on a small subset
python code/main.py
```

## Code Style

### Python Style Guide

- **Line Length**: Maximum 88 characters (Black)
- **Imports**: Sorted with isort, grouped by standard library, third-party, local
- **Type Hints**: Required for all function signatures
- **Docstrings**: Google style for all public functions

### Example

```python
def compute_correlation(
 df: pd.DataFrame,
 method: str = 'pearson'
) -> pd.DataFrame:
 """
 Compute correlation matrix for the dataset.

 Args:
 df: Input DataFrame with numeric columns.
 method: Correlation method ('pearson' or 'spearman').

 Returns:
 pd.DataFrame: Correlation matrix.

 Raises:
 ValueError: If method is not 'pearson' or 'spearman'.
 """
 if method not in ['pearson', 'spearman']:
 raise ValueError(f"Method must be 'pearson' or 'spearman', got {method}")

 corr_matrix = df.corr(method=method)
 return corr_matrix
```

## Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build process or auxiliary tool changes

### Examples

```
feat(stats): add clustering coefficient calculation

Implements average clustering coefficient as a network statistic.
Uses networkx built-in function with edge weighting.

Closes #123
```

```
fix(loaders): handle missing UCI dataset gracefully

Raises FileNotFoundError instead of silent failure when
dataset cannot be fetched from UCI repository.

Related to Constitution VII compliance.
```

## Pull Request Process

### 1. Create a PR

```bash
# Push your branch
git push origin feature/your-feature-name

# Create PR on GitHub
```

### 2. PR Checklist

- [ ] All tests pass
- [ ] Code is formatted (black, isort)
- [ ] No linting errors (flake8)
- [ ] Documentation updated
- [ ] Type hints added
- [ ] Tests added for new features
- [ ] No hardcoded values or synthetic data
- [ ] Follows project architecture

### 3. Review Process

1. Automated checks run (tests, linting)
2. Maintainer reviews code
3. Address feedback
4. Merge after approval

## Documentation

### What to Document

- New public functions and classes
- Configuration options
- Usage examples
- API changes
- Breaking changes

### Where to Document

- `README.md`: Overview and quick start
- `docs/api_reference.md`: API documentation
- `docs/usage_guide.md`: Detailed usage instructions
- `docs/contributing.md`: Contribution guidelines
- Inline docstrings: Code documentation

## Testing Guidelines

### Unit Tests

- Test individual functions
- Mock external dependencies
- Cover edge cases
- Place in `tests/unit/`

### Integration Tests

- Test complete workflows
- Use real data where possible
- Test end-to-end scenarios
- Place in `tests/integration/`

### Test Naming

```python
def test_function_name_specific_scenario():
 """Test description."""
 # Arrange
 # Act
 # Assert
```

## Data Integrity

### Important Rules

- **NEVER** use synthetic data for final results
- **NEVER** hardcode dataset lists
- **ALWAYS** load from real UCI repository
- **ALWAYS** fail loudly if data fetch fails
- **ALWAYS** verify data integrity

### Synthetic Data Usage

Synthetic data is ONLY allowed for:
- Validation tests (T016, T016b)
- Unit tests with known properties
- Development debugging

## Performance Considerations

- Optimize for CPU-only execution
- Avoid loading entire datasets into memory when possible
- Use streaming for large datasets
- Profile before optimizing

## Common Tasks

### Adding a New Statistic

1. Add function to `stats_engine.py`
2. Update `calculate_stats()` to include new statistic
3. Add test in `tests/unit/test_stats_engine.py`
4. Update documentation

### Adding a New Visualization

1. Add function to `viz.py`
2. Update `main.py` to call the function
3. Add test in `tests/integration/`
4. Update `docs/api_reference.md`

### Modifying Configuration

1. Update `code/config.py`
2. Update `README.md` and `docs/usage_guide.md`
3. Test with new configuration
4. Add note to changelog

## Questions?

If you have questions:
1. Check existing issues and documentation
2. Open a new issue with your question
3. Tag maintainers if needed

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Acknowledgments

Thank you to all contributors who have helped make this project better!
