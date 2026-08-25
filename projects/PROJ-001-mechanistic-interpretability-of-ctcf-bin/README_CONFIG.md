# Configuration Management Guide

This document describes how to configure the CTCF binding site selection project, including API keys and local paths.

## Quick Start

1. **Generate a sample configuration file:**
 ```bash
 python code/config/config_loader.py sample -o config/config.yaml
 ```

2. **Edit `config/config.yaml`:**
 - Set `api.encode_api_key` to your ENCODE API key.
 - Adjust paths if your project structure differs from the default.

3. **Set environment variables (optional but recommended):**
 ```bash
 export ENCODE_API_KEY="your-api-key-here"
 export PROJECT_CONFIG="/path/to/config.yaml"
 ```

4. **Validate your setup:**
 ```bash
 python code/config/config_loader.py validate
 ```

## Configuration Structure

The configuration file (`config.yaml`) supports the following sections:

### `paths`
Defines root directories for data and outputs.
- `data_root`: Root directory for all data files.
- `processed_data`: Directory for processed datasets.
- `models`: Directory for saved model weights.
- `interpretation`: Directory for interpretability outputs.
- `figures`: Directory for generated plots.

### `api`
Configuration for external APIs.
- `encode_api_key`: Your ENCODE API key (can also be set via `ENCODE_API_KEY` env var).
- `encode_base_url`: Base URL for ENCODE API (default: ` Name or service not known)"))]).

### `model`
Model training and inference settings.
- `device`: Execution device (`cpu` or `cuda`).
- `seed`: Random seed for reproducibility.

## API Keys

### ENCODE API Key
To obtain an ENCODE API key:
1. Register at https://www.encodeproject.org.
2. Navigate to your user profile and generate an API key.
3. Set the key in `config.yaml` or export it as an environment variable:
 ```bash
 export ENCODE_API_KEY="your-key"
 ```

**Security Note:** Never commit your API key to version control. Add `config.yaml` to `.gitignore` if it contains secrets.

## Path Resolution

Paths in the configuration file are resolved relative to the project root. If absolute paths are provided, they are used as-is.

Example:
```yaml
paths:
 data_root: data # Resolved as <project_root>/data
 models: /absolute/path/to/models # Used as-is
```

## Command Line Interface

The configuration module includes a CLI for common tasks:

- **Generate sample config:**
 ```bash
 python code/config/config_loader.py sample
 ```

- **Validate manifest existence:**
 ```bash
 python code/config/config_loader.py validate
 ```

- **Show resolved paths:**
 ```bash
 python code/config/config_loader.py paths
 ```

## Troubleshooting

- **"Data manifest not found"**: Ensure you have completed the data gap resolution tasks (T003-T007) and that `data/manifest.json` exists.
- **"ENCODE API key not found"**: Set the `ENCODE_API_KEY` environment variable or add it to `config.yaml`.
- **Path errors**: Verify that your `config.yaml` paths are correct and that the directories exist or can be created.