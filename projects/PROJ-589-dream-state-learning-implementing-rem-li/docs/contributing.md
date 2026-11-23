# Contributing to Dream-State Learning

Thank you for your interest in contributing to this research project!
This document outlines the guidelines for contributing to the Dream-State
Learning implementation.

## Code of Conduct

This project is a research initiative. We encourage:
- Respectful and constructive feedback
- Evidence-based discussions
- Clear documentation of assumptions and limitations
- Recognition of the speculative nature of the research

## How to Contribute

### Reporting Issues

When reporting issues, please include:
1. **Environment details**: Python version, OS, hardware specs
2. **Error logs**: Full traceback from `data/logs/`
3. **Reproduction steps**: Exact commands that triggered the issue
4. **Expected vs. actual behavior**: Clear description of the problem

### Suggesting Changes

Before proposing significant changes:
1. Check existing issues and pull requests
2. Consider the research implications
3. Provide a clear rationale for the change
4. Include test coverage for new functionality

### Development Workflow

1. **Fork the repository** and create a feature branch
2. **Implement your changes** following the coding standards below
3. **Run tests**: `pytest tests/`
4. **Validate quickstart**: `python scripts/validate_quickstart.py`
5. **Submit a pull request** with a clear description

## Coding Standards

### Python Style

- **Formatting**: Use Black (auto-format)
- **Linting**: Use Ruff (no warnings allowed)
- **Type hints**: Required for all function signatures
- **Docstrings**: Google-style docstrings for all public functions

### File Organization

- **Code**: `code/` directory for implementation
- **Tests**: `tests/` directory (unit, integration, contract)
- **Data**: `data/` for datasets, checkpoints, and results
- **Docs**: `docs/` for documentation
- **Scripts**: `code/scripts/` for utility scripts

### Import Conventions

Follow the existing import structure:
```python
# Absolute imports from project modules
from config import Config
from data.loader import load_glue_subset
from models.trainer import Trainer
from utils.logger import get_logger
```

Do NOT invent new module names or import paths. Use only the APIs
documented in `docs/api_reference.md`.

### Testing Requirements

All new functionality must include:
- **Unit tests**: `tests/unit/` for isolated components
- **Integration tests**: `tests/integration/` for multi-component workflows
- **Contract tests**: `tests/contract/` for schema validation

Tests must run on CPU-only environments with limited resources.

## Documentation Standards

### Code Documentation

Every public function must have:
- A clear docstring describing purpose
- Parameter descriptions
- Return value descriptions
- Exception documentation

### User Documentation

Documentation in `docs/` should:
- Explain the "why" not just the "how"
- Include examples and use cases
- Note limitations and constraints
- Reference relevant research

### Research Documentation

When documenting research decisions:
- Cite the original specification or plan
- Note any divergences from the spec
- Explain the rationale for architectural choices
- Acknowledge limitations

## Research Integrity

### Data Usage

- **Real data only**: Never fabricate or hard-code fake data
- **Verified sources**: Use only approved dataset sources (GLUE/SuperGLUE)
- **Checksum verification**: All downloads must be verified
- **No synthetic fallbacks**: Fail loudly if real data is unavailable

### Experimental Results

- **Reproducibility**: All experiments must be reproducible with seeds
- **Statistical rigor**: Use appropriate statistical tests (paired t-test, etc.)
- **Transparency**: Report limitations and constraints honestly
- **No cherry-picking**: Report all results, not just favorable ones

### Speculation vs. Implementation

- Clearly distinguish between:
 - Implemented features (code that runs)
 - Speculative ideas (research hypotheses)
 - Planned features (not yet implemented)
- Avoid presenting speculation as fact
- Acknowledge when implementation diverges from specification

## Pull Request Process

1. **Title**: Clear, descriptive title
2. **Description**:
 - What problem does this solve?
 - How does it solve it?
 - Any breaking changes?
3. **Testing**:
 - All tests pass
 - New tests included
 - Quickstart validation passes
4. **Documentation**:
 - Code docstrings updated
 - User docs updated if needed
5. **Review**:
 - Address all review comments
 - Squash commits if appropriate

 ## License

This project is research code. Contributions are accepted under the same
terms as the original project.

## Questions?

For questions about:
- **Implementation**: Check `docs/api_reference.md`
- **Usage**: Check `quickstart.md`
- **Research**: Check `specs/001-dream-state-learning-implementing-rem-li/`
- **Issues**: Open a GitHub issue with detailed information

Thank you for contributing to this research initiative!