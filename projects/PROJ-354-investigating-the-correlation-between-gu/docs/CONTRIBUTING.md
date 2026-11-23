# Contributing Guidelines

## Development Workflow

1. **Fork the repository** and create a feature branch
2. **Implement changes** following the coding standards
3. **Write tests** for new functionality
4. **Run the full test suite** before committing
5. **Update documentation** if APIs or workflows change
6. **Submit a pull request** with clear description

## Coding Standards

### Python Style

- Follow PEP 8 guidelines
- Use Black for formatting (`black code/`)
- Use Ruff for linting (`ruff check code/`)
- Type hints required for all function signatures
- Docstrings in Google or NumPy format

### Code Organization

- Keep functions focused and single-purpose
- Use streaming for large data operations
- Handle errors gracefully with custom exceptions
- Log all significant operations
- Avoid hard-coded paths (use `config.get_path()`)

### Testing Requirements

- Unit tests for all new functions
- Integration tests for pipeline components
- Tests must run against real data when possible
- Mock external services only when necessary

## Data Handling

### Real Data Only

- Never fabricate data or use synthetic placeholders in production
- All data loaders must fail loudly if real data cannot be fetched
- Streaming required for datasets >7GB
- PII must be masked before any analysis

### Memory Constraints

- Assume 7GB RAM limit
- Use batch processing for large operations
- Monitor memory usage with `perf_monitor.py`
- Implement garbage collection for long-running processes

## Documentation

### Required Updates

When modifying code:
- Update docstrings for changed functions
- Add examples to `quickstart.md` if workflows change
- Update `api_reference.md` for API changes
- Document new configuration options

### Documentation Standards

- Clear, concise language
- Include code examples where helpful
- Reference related files and modules
- Maintain consistent formatting

## Pull Request Process

1. **Title**: Use format `[T0XX] Brief description`
2. **Description**: Explain what changed and why
3. **Testing**: List tests added or modified
4. **Documentation**: Note any documentation updates
5. **Breaking Changes**: Clearly mark any breaking changes

## Review Guidelines

Reviewers should check:
- Code quality and style compliance
- Test coverage and correctness
- Documentation completeness
- Performance implications
- Security considerations (PII handling)

## Issue Reporting

When reporting issues:
- Provide clear reproduction steps
- Include error messages and stack traces
- Specify environment (Python version, OS, dependencies)
- Note whether the issue affects real data or synthetic tests

## Security Considerations

- Never commit API keys or tokens
- Use environment variables or keyring for credentials
- Mask PII in all data operations
- Follow UK Biobank data usage policies

## Performance Guidelines

- Profile code before optimizing
- Use streaming for large datasets
- Batch operations when possible
- Monitor memory usage in production
- Document performance-critical sections

## Release Process

1. Complete all tasks for a user story
2. Run full pipeline validation
3. Update version in `requirements.txt` if needed
4. Create release tag
5. Update changelog

## Contact

For questions or concerns:
- Open an issue in the repository
- Contact the project maintainer
- Refer to project documentation
