# Project Scripts

This directory contains utility scripts for project maintenance.

## Scripts

- `lint.sh`: Runs ruff and black (check mode) to verify code quality.
- `format.sh`: Runs black and ruff (fix mode) to automatically format code.
- `install_dev_deps.sh`: Installs development dependencies from `requirements-dev.txt`.

## Usage

Ensure you are in the project root and have the virtual environment activated:

```bash
source code/.venv/bin/activate
```

Then run scripts:

```bash
# Install dev tools if not already done
bash code/scripts/install_dev_deps.sh

# Format code
bash code/scripts/format.sh

# Check linting
bash code/scripts/lint.sh
```

Alternatively, use the Makefile:

```bash
make format
make lint
```