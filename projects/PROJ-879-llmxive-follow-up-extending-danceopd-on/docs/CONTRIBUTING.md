# Contributing to llmXive

## Development Workflow

1. **Read the Plan**: Before starting, review `plan.md` and `tasks.md`
2. **Understand the Story**: Each task belongs to a user story (US1, US2, US3)
3. **Write Tests First**: For test tasks, ensure tests fail before implementation
4. **Implement the Task**: Write complete, executable code (no stubs)
5. **Verify**: Run tests and ensure the task completes successfully
6. **Document**: Update documentation as needed
7. **Commit**: Commit after each task or logical group

## Code Style

- **Formatting**: Use black (configured in `pyproject.toml` or `setup.cfg`)
- **Linting**: Use ruff for linting
- **Type Hints**: Use type hints for all function signatures
- **Docstrings**: Use Google-style docstrings for all public functions
- **Imports**: Import only names that exist in the API surface

## File Organization

- **Code**: `code/` directory
- **Tests**: `tests/unit/` and `tests/integration/`
- **Data**: `data/raw/`, `data/processed/`, `data/results/`
- **Models**: `models/`
- **Specs**: `specs/contracts/` for JSON schemas
- **Docs**: `docs/` for documentation

## Testing Guidelines

### Unit Tests
- Test individual functions
- Mock external dependencies where appropriate
- Run with `pytest tests/unit/`

### Integration Tests
- Test end-to-end pipeline stages
- Use real data where possible
- Run with `pytest tests/integration/`

### Test Tasks
- Test tasks are optional unless explicitly requested
- If included, write them FIRST and ensure they FAIL before implementation
- Tests must validate the actual requirements, not just pass trivially

## Data Integrity

- **No Synthetic Data**: All data must come from real sources
- **Fail Loudly**: If real data cannot be fetched, raise an error
- **Validation**: All data validated against JSON schemas
- **Versioning**: All datasets versioned with checksums

## Common Pitfalls

### 1. Stub Code
- **Don't**: Write `pass` or `NotImplementedError`
- **Do**: Write complete, working code

### 2. Fabricated Data
- **Don't**: Generate synthetic/fake data to bypass real data fetching
- **Do**: Fetch from real sources (ImageNet, LAION via HF)

### 3. Silent Fallbacks
- **Don't**: Fall back to mock data when real data fails
- **Do**: Raise an error and let the execution stage discover the issue

### 4. Incorrect Imports
- **Don't**: Invent names that don't exist in the API surface
- **Do**: Import only names that are defined in sibling files

### 5. Partial Implementation
- **Don't**: Leave TODOs or incomplete functions
- **Do**: Complete the entire task in one go

## Review Process

1. **Self-Check**: Ensure all requirements are met
2. **Peer Review**: Another developer reviews the implementation
3. **Automated Verification**: Run automated tests and validation
4. **Integration**: Merge into main branch

## Documentation

- **README.md**: High-level project overview
- **docs/PROJECT_OVERVIEW.md**: Research methodology and questions
- **docs/ARCHITECTURE.md**: System architecture and data flow
- **docs/CONTRIBUTING.md**: This file
- **docs/QUICKSTART.md**: Step-by-step guide to run the pipeline

## Support

For questions or issues:
1. Check existing documentation
2. Review `tasks.md` for task-specific details
3. Contact the project maintainers
