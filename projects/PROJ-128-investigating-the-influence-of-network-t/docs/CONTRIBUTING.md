# Contributing Guide

Thank you for your interest in contributing to this project! This document outlines the process for contributing code, documentation, and research artifacts.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on scientific rigor and reproducibility

## Getting Started

### 1. Fork and Clone

```bash
git clone
cd PROJ-128-investigating-the-influence-of-network-t
```

### 2. Setup Environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

## Development Workflow

### Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch for upcoming features
- `feature/TXXX`: New feature or task (e.g., `feature/T050`)
- `bugfix/XXX`: Bug fixes

### Commit Messages

Follow conventional commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

Example:
```
docs(T050): Update README with quick start guide

Added installation instructions and project structure diagram.

Closes #123
```

## Testing Requirements

### Before Submitting PR

1. Run all tests:
```bash
pytest tests/ -v
```

2. Check code style:
```bash
flake8 code/
black --check code/
```

3. Validate pipeline:
```bash
python code/validate_quickstart.py
```

### Test Writing Guidelines

- Tests must fail before implementation (TDD approach)
- Use real data where possible (no synthetic mocks)
- Test edge cases (empty data, convergence failures)
- Document test purpose in docstrings

## Code Style

- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type annotations for function signatures
- **Docstrings**: Google or NumPy style for all public functions
- **Imports**: Group by standard library, third-party, local modules

Example:
```python
"""Module description.

Args:
 data: Input data array.
 threshold: Density threshold value.

Returns:
 Dictionary of graph metrics.
"""
from typing import Dict, List, Optional

import numpy as np
import networkx as nx

def calculate_metrics(data: np.ndarray, threshold: float) -> Dict[str, float]:
 """Calculate graph metrics."""
 pass
```

## Documentation Standards

### When to Update Docs

- New features or APIs
- Changed behavior or parameters
- Updated dependencies
- New data sources or formats

### Documentation Files

- `README.md`: Project overview and quick start
- `ARCHITECTURE.md`: System design and component interactions
- `CONTRIBUTING.md`: This file
- `docs/api/`: API reference (if applicable)

## Pull Request Process

1. **Create Branch**: From `develop` or `main`
2. **Implement Changes**: Follow coding standards
3. **Write Tests**: Ensure coverage for new code
4. **Update Docs**: Reflect changes in documentation
5. **Run Validation**: All tests and checks must pass
6. **Submit PR**: Include clear description and task references

### PR Template

```markdown
## Description
[Brief description of changes]

## Related Tasks
- Closes #T050
- Related to #T051

## Changes
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual validation complete

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
```

## Review Guidelines

### For Reviewers

- Check for code quality and style
- Verify tests cover edge cases
- Ensure documentation is accurate
- Validate against task requirements
- Confirm no fabrication of data/results

### For Authors

- Address feedback promptly
- Be open to suggestions
- Provide context for design decisions
- Update PR description if scope changes

## Data Integrity

**Critical**: All data must come from real, verified sources.
- Never fabricate results or use synthetic data as a fallback
- If real data is unavailable, the pipeline should fail loudly
- Document all data sources and download procedures

## Performance Considerations

- Optimize for CPU-only environments
- Use chunked processing for large datasets
- Monitor memory usage (target: <7GB RAM)
- Avoid GPU acceleration unless explicitly authorized

## Release Process

1. Version bump in `pyproject.toml` or `VERSION`
2. Update `CHANGELOG.md` with changes
3. Tag release: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. Create GitHub release with notes

## Questions?

If you have questions or need clarification:
- Check existing issues/PRs
- Open a new issue with label `question`
- Contact maintainers via email or Slack

Thank you for contributing!
