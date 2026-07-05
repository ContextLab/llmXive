# Environment Setup Guide

## Overview

This project uses environment variables and configuration files to manage:
- API keys for external services (Materials Project)
- Random seeds for reproducible experiments
- Path configurations for data and model storage

## Quick Start

1. **Copy the example environment file:**
 ```bash
 cp.env.example.env
 ```

2. **Edit `.env` with your credentials:**
 ```bash
 nano.env
 ```

3. **Set your Materials Project API key:**
 - Register at https://materialsproject.org
 - Get your API key from the dashboard
 - Add it to `.env`:
 ```
 MATERIALS_PROJECT_API_KEY=your_actual_api_key_here
 ```

4. **Set a random seed (optional but recommended):**
 ```
 RANDOM_SEED=42
 ```

## Configuration Management

The `code/config.py` module provides a centralized configuration manager:

```python
from config import get_config, initialize_environment

# Get the configuration instance
config = get_config()

# Access API keys
mp_key = config.get_api_key('materials_project')

# Access random seed
seed = config.get_random_seed()

# Set a custom seed
config.set_random_seed(123)

# Get project paths
data_path = config.get_path('data_raw')
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MATERIALS_PROJECT_API_KEY` | Materials Project API key | Yes | None |
| `RANDOM_SEED` | Random seed for reproducibility | No | 42 |

## Security Best Practices

1. **Never commit `.env` files** - They are in `.gitignore`
2. **Use environment variables in CI/CD** - Set secrets in your CI platform
3. **Rotate API keys regularly** - Update keys if compromised
4. **Use minimal permissions** - Request only necessary API access

## Troubleshooting

### API Key Not Found

If you see warnings about missing API keys:
- Verify `.env` file exists in project root
- Check that `MATERIALS_PROJECT_API_KEY` is set correctly
- Ensure no typos in the environment variable name

### Random Seed Not Working

If results are not reproducible:
- Verify `RANDOM_SEED` is set in `.env`
- Check that all random operations use the configured seed
- Ensure `pin_seed()` is called at the start of experiments

## Advanced Usage

### Custom Seed Initialization

```python
from config import initialize_environment

# Initialize with custom seed
initialize_environment(seed=12345)
```

### Custom.env File Location

```python
from config import initialize_environment
from pathlib import Path

# Load from specific.env file
initialize_environment(env_file=Path('/path/to/custom.env'))
```

### Programmatic Configuration

```python
from config import get_config

config = get_config()

# Ensure directories exist
config.ensure_directories()

# Export configuration (without sensitive data)
config_dict = config.to_dict()
```
