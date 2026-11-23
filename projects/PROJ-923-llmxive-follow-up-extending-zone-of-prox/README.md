# llmXive Follow-up: Extending "Zone of Proximal Policy Optimization"

## Code Quality Tools

This project uses **Black** for code formatting and **Ruff** for linting.

### Installation

```bash
pip install -r requirements.txt
```

### Usage

**Format code:**
```bash
black code/ tests/
# Or use the Makefile target:
make format
```

**Lint code:**
```bash
ruff check code/ tests/
# Or use the Makefile target:
make lint
```

**Check formatting (without modifying):**
```bash
black --check code/ tests/
```

**Run all checks:**
```bash
make check-format
```

### Configuration

- **Black**: Configured in `pyproject.toml` with line length 88 and target Python 3.9+.
- **Ruff**: Configured in `pyproject.toml` and `.ruff.toml` to enforce PEP 8, import sorting, and bugbear checks.

### CI/CD Integration

The linting and formatting checks should be run in your CI pipeline before merging.
Example GitHub Actions step:
```yaml
- name: Lint and Format Check
 run: |
 make check-format
```