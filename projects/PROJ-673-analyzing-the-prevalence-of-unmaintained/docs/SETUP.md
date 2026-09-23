# Setup Instructions

This document provides detailed setup instructions for the project infrastructure.

## Environment Variables

The following environment variables must be configured before running the pipeline:

### Required

- `NPM_API_KEY`: API key for NPM registry (optional for public packages, recommended for higher rate limits)
- `GITHUB_TOKEN`: GitHub personal access token with `public_repo` scope

### Optional

- `RATE_LIMIT`: Maximum requests per minute (default: 60)
- `TOP_PACKAGES`: Number of top packages to analyze (default: 100)

### Setting Environment Variables

#### Method 1: Export in Shell (Linux/Mac)
```bash
export NPM_API_KEY="your_key_here"
export GITHUB_TOKEN="your_token_here"
```

#### Method 2: Create.env File
Create a `.env` file in the project root:
```
NPM_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
RATE_LIMIT=60
TOP_PACKAGES=100
```

Then load it with:
```bash
source.env
```

#### Method 3: Windows PowerShell
```powershell
$env:NPM_API_KEY="your_key_here"
$env:GITHUB_TOKEN="your_token_here"
```

## Virtual Environment Setup

1. Create virtual environment:
 ```bash
 python -m venv.venv
 ```

2. Activate virtual environment:
 - Linux/Mac: `source.venv/bin/activate`
 - Windows: `.venv\Scripts\activate`

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Linting and Formatting

The project uses `ruff` for linting and `black` for formatting.

### Install Tools
```bash
pip install ruff black
```

### Run Linter
```bash
ruff check.
```

### Run Formatter
```bash
black --check.
```

### Auto-fix Issues
```bash
ruff check --fix.
black.
```

## Project Structure

The project follows a standard Python package structure:

- `code/src/models/`: Pydantic data models
- `code/src/services/`: API client implementations
- `code/src/analysis/`: Statistical analysis modules
- `code/src/cli/`: Command-line interfaces
- `code/src/utils/`: Utility functions
- `code/src/config/`: Configuration management
- `code/tests/`: Test suites
- `code/data/raw/`: Cached API responses
- `code/data/processed/`: Analysis outputs
- `code/docs/`: Documentation

## Verification

After setup, verify the installation:

```bash
# Check Python version
python --version # Should be 3.11+

# Check dependencies
pip list | grep -E "requests|pandas|scipy|statsmodels|matplotlib|pyyaml|pydantic|networkx"

# Verify directory structure
ls -R code/src/
```

## Troubleshooting

### Missing Dependencies
If you encounter `ModuleNotFoundError`, ensure you're in the virtual environment and dependencies are installed:
```bash
source.venv/bin/activate
pip install -r requirements.txt
```

### Permission Errors
If you encounter permission errors when writing to `data/` directories:
```bash
chmod -R 755 code/data/
```

### API Rate Limiting
If you encounter rate limit errors, reduce the `TOP_PACKAGES` value or wait between runs. The pipeline implements exponential backoff automatically.