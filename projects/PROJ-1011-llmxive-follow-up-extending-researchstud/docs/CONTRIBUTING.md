# Contributing to llmXive

Thank you for your interest in contributing to the llmXive automated research pipeline!

## Code of Conduct

- Be respectful and constructive
- Follow the existing code style
- Write clear commit messages
- Document your changes

## Development Setup

1. Fork the repository
2. Create a feature branch:
 ```bash
 git checkout -b feature/your-feature-name
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
4. Set up pre-commit hooks (optional):
 ```bash
 pre-commit install
 ```

## Development Workflow

### 1. Understand the Task

Before implementing:
- Read the task description in `tasks.md`
- Review the API surface in existing files
- Check dependencies and execution order

### 2. Implement the Feature

Guidelines:
- **No stubs**: Write complete, runnable code
- **No synthetic data**: Use real sources or fail loudly
- **Follow API surface**: Import only existing names
- **Stay in project tree**: Use relative paths under `code/`, `data/`, `tests/`

### 3. Write Tests

For each feature:
- Add unit tests in `tests/unit/`
- Test edge cases and error conditions
- Ensure tests fail before implementation (TDD)

### 4. Run Tests

```bash
pytest tests/unit/ -v
```

All tests must pass before committing.

### 5. Validate Benchmark

```bash
python code/utils/benchmark_validator.py
```

Ensure total runtime stays under 6 hours.

### 6. Update Documentation

If your change affects:
- API surface: Update `docs/pipeline_architecture.md`
- Usage: Update `docs/quickstart.md`
- Configuration: Update `docs/README.md`

### 7. Commit

Write a clear commit message:
```bash
git commit -m "feat: implement T043 documentation updates"
```

Format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions
- `refactor:` for code refactoring

### 8. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Create a PR with:
- Description of changes
- Linked task ID (e.g., "Closes T043")
- Test results

## Code Style

### Python

- Use `black` for formatting
- Use `ruff` for linting
- Type hints for all function signatures
- Docstrings for all public functions

Example:
```python
def process_data(data: List[Dict]) -> List[Dict]:
 """
 Process input data and return cleaned records.

 Args:
 data: List of raw data records

 Returns:
 List of processed records with normalized fields
 """
 pass
```

### File Organization

- Keep modules focused (single responsibility)
- Group related functions
- Use `utils/` for shared helpers
- Keep tests co-located with features

## Testing Guidelines

### Unit Tests

- Test individual functions
- Mock external dependencies
- Assert specific behaviors

Example:
```python
def test_validate_fetch_status_403_raises():
 with pytest.raises(DataFetchError) as exc_info:
 validate_fetch_status(response_403)
 assert "403" in str(exc_info.value)
```

### Integration Tests

- Test end-to-end flows
- Use real data where possible
- Verify artifact outputs

## Documentation Standards

### Inline Comments

- Explain "why", not "what"
- Keep comments up-to-date with code

### Docstrings

- Use Google or NumPy style
- Include Args, Returns, Raises
- Add examples for complex functions

### README Updates

- Keep instructions current
- Document configuration options
- Include troubleshooting tips

## Review Process

1. Automated checks run (tests, lint, benchmark)
2. Maintainer reviews code and documentation
3. Feedback provided; iterate if needed
4. Approved PR is merged

## Common Pitfalls

### ❌ Creating Synthetic Data

**Wrong**:
```python
if fetch_failed:
 return generate_synthetic_data()
```

**Right**:
```python
if fetch_failed:
 raise DataFetchError("Failed to fetch from real source")
```

### ❌ Hardcoding Model Names

**Wrong**:
```python
model = SentenceTransformer("all-MiniLM-L6-v2")
```

**Right**:
```python
model_name = get_model_config("EMBEDDING_MODEL")
model = SentenceTransformer(model_name)
```

### ❌ Ignoring Memory Constraints

**Wrong**:
```python
data = load_full_dataset() # May exceed RAM
```

**Right**:
```python
data = stream_and_sample(n=500, seed=42)
```

## Questions?

If you have questions:
- Check existing issues and PRs
- Read `docs/README.md` and `docs/pipeline_architecture.md`
- Open a new issue for discussion

## License

By contributing, you agree that your contributions will be licensed under the project's license.
