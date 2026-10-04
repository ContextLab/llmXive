# Contributing to llmXive Network Topology

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community

## Getting Started

1. **Fork the repository**
2. **Clone your fork**:
 ```bash
 git clone
 cd llmXive-network-topology
 ```
3. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate
 ```
4. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 pip install pytest black flake8 # Development tools
 ```

## Development Workflow

1. **Create a feature branch**:
 ```bash
 git checkout -b feature/your-feature-name
 ```
2. **Make your changes**
3. **Run tests**:
 ```bash
 pytest tests/
 ```
4. **Format code**:
 ```bash
 black code/
 flake8 code/
 ```
5. **Commit your changes**:
 ```bash
 git commit -m "Add: description of your changes"
 ```
6. **Push to your fork**:
 ```bash
 git push origin feature/your-feature-name
 ```
7. **Open a pull request**

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows the project's style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated (if applicable)
- [ ] No new warnings or errors
- [ ] Associational language compliance verified (for reports)

### Pull Request Description

Include:
- Clear description of changes
- Related issue numbers (if applicable)
- Testing performed
- Any breaking changes

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints where possible
- Write docstrings for all functions
- Keep functions focused and small

### Documentation

- Update `docs/` when adding features
- Include examples in docstrings
- Keep README and quickstart up to date

### Testing

- Write tests for new features
- Maintain test coverage
- Tests should fail first (TDD approach)

## Associational Language Compliance

When modifying reports or documentation:
- Avoid causal language (predict, cause, drive, determine)
- Use associational terms (associated with, correlates with)
- Run `python code/reports/audit_associational_language.py` to verify

## Data Integrity

- Never fabricate data or results
- Always use real HCP data from OpenNeuro
- If real data is unavailable, let the loader fail loudly
- Document any data limitations honestly

## Review Process

1. Automated checks run on PR
2. Maintainers review code and tests
3. Feedback provided and addressed
4. PR merged after approval

## Questions?

- Check existing issues
- Read the documentation in `docs/`
- Open a new issue for questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
