# Environment Variable Setup for Solar Irradiance Reconstruction Project

## Overview

This project uses environment variables to manage data paths and configuration settings.
This approach allows for flexible deployment across different environments (local, CI/CD, production)
without modifying code.

## Setup Instructions

### 1. Copy the Example Environment File

A template file `code/.env.example` is provided. Copy it to `code/.env` in your project root:

```bash
cp code/.env.example code/.env
```

### 2. Configure Your Paths

Edit `code/.env` and set the appropriate paths for your environment:

```env
# Root directory for all data files
DATA_ROOT_PATH=/absolute/path/to/your/data

# Raw data directory (downloads)
DATA_RAW_PATH=/absolute/path/to/your/data/raw

# Processed data directory
DATA_PROCESSED_PATH=/absolute/path/to/your/data/processed

# Model artifacts directory
MODEL_ARTIFACTS_PATH=/absolute/path/to/your/code/models/artifacts

# Figures and reports directory
DATA_FIGURES_PATH=/absolute/path/to/your/data/figures
```

### 3. Optional: Override Data Sources

If you need to use alternative data sources, you can override the default URLs:

```env
SILSO_URL= Name or service not known)"))]
SORCE_URL= Name or service not known)"))]
```

## How It Works

The `code/env_manager.py` module provides the following functionality:

1. **Loading**: Automatically loads variables from `code/.env` if it exists.
2. **Fallback**: Falls back to `os.environ` if variables are not in the file.
3. **Defaults**: Uses sensible defaults relative to the project root if no environment variable is set.
4. **Validation**: Provides `validate_data_paths()` to check that directories exist.

### Usage in Code

```python
from code.env_manager import setup_environment, get_data_path

# Full setup (loads.env, validates paths, returns config dict)
config = setup_environment()
data_root = config["data_root"]

# Direct path resolution
raw_data_path = get_data_path(env_var_name="DATA_RAW_PATH", default="data/raw")

# Get specific values
silso_url = get_env_var("SILSO_URL", default="https://www.sidc.be/...")
```

## Best Practices

1. **Never commit `.env` files**: Add `code/.env` to `.gitignore`.
2. **Use `.env.example` as a template**: Commit the example file with placeholder values.
3. **Document required variables**: Keep this README up to date.
4. **Use absolute paths**: For data directories, absolute paths are recommended to avoid ambiguity.
5. **Validate in CI/CD**: Ensure your CI/CD pipeline sets these variables or uses appropriate defaults.

## Troubleshooting

### "Path does not exist" warnings

If you see warnings about missing paths, ensure:
1. The `.env` file exists in `code/`
2. The paths specified are absolute and correct
3. The directories actually exist (create them if needed)

### Variables not loading

Check that:
1. You are running the script from the project root
2. The `.env` file has no syntax errors (no extra spaces around `=`)
3. File permissions allow reading the `.env` file
