# llmXive Research Pipeline: Dietary Fiber and Gut Microbiome

## Linting and Formatting

This project uses **ruff** for linting and **black** for code formatting.

### Installation

Install dependencies including linting tools:
```bash
pip install -r requirements.txt
```

### Configuration

Configuration files are provided in the project root:
- `.ruff.toml`: Ruff linting rules
- `.black.toml`: Black formatting rules

### Usage

Run linting:
```bash
ruff check.
```

Format code:
```bash
black.
```

Run both checks before committing:
```bash
./scripts/config_linters.sh
```
