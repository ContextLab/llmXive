# Project Directory Setup

This document describes the project directory structure created by task T001b.

## Directories Created

The following directories are created at the repository root:

- `data/raw/` - Raw data files downloaded from external sources (e.g., UCI datasets)
- `data/derived/` - Processed and derived data files (subsamples, logs, etc.)
- `results/` - Simulation results and analysis outputs (JSON files)
- `contracts/` - Schema definitions and contract files for data validation
- `code/` - Source code modules (created by T001a)
- `tests/` - Test modules (created by T001a)

## Usage

To create these directories, run:

```bash
python code/setup_directories.py
```

Or from the project root:

```bash
python -m code.setup_directories
```

The script is idempotent - running it multiple times will not cause errors if directories already exist.

## Verification

You can verify the directories exist by running:

```bash
ls -la
```

Or using the provided test:

```bash
pytest tests/test_setup_directories.py -v
```