# Project PROJ-215: Investigating the Relationship Between Gut Microbiome Composition and Mental Health

## Environment Configuration

This project uses environment variables for configuration management.

### Setup

1. Copy the example file to a local `.env` file:
 ```bash
 cp.env.example.env
 ```
2. Edit `.env` to set your specific values (e.g., `RANDOM_SEED`, `VERBOSE`).
3. Ensure `python-dotenv` is installed (included in `requirements.txt`).

### Usage

The `code/config_loader.py` module handles loading these variables.
To initialize the configuration in your scripts, call:
```python
from code.config_loader import initialize_config
config = initialize_config()
```

### Available Variables

- `RANDOM_SEED`: Integer seed for reproducibility (default: 42)
- `VERBOSE`: Boolean flag for logging verbosity (default: false)
- `DATA_PATH`: Optional path override for data directories
- `QIITA_API_KEY`: Optional API key for direct Qiita access (if applicable)