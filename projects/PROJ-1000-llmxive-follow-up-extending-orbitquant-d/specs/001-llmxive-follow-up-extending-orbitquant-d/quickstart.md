# Quickstart: Project Skeleton Initialization

This guide explains how to set up the project skeleton and verify that the basic configuration is working.

## Prerequisites
- Python 3.11 or newer
- Git

## Setup

```bash
# 1. Clone the repository and navigate to the project root
git clone <repo-url>
cd projects/PROJ-1000-llmxive-followup-extending-orbitquant-d

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Initialize the Project Skeleton

The project provides a command-line entry point that creates the required
directory structure under `code/` and prints a confirmation message.

```bash
python -m code.main --phase init
```

You should see the following output:

```
Initialization complete
```

This indicates that:
- All required sub‑directories under `code/` (analysis, models, quantization, evaluation, utils, runners, data, validation) have been created, each with an `__init__.py` package marker.
- The `tests/` directory is in place (with a placeholder test).
- The `requirements.txt` file lists `torch` among its dependencies.

## Verification

You can run a few quick checks to confirm the setup:

```bash
# Count the number of sub‑directories under code/
find code/ -type d | wc -l   # should be ≥ 8

# Ensure the config module imports without error
python -c "import code.config"

# Verify that the requirements file lists torch
grep -c "torch" requirements.txt   # should be ≥ 1

# Confirm the init phase runs and prints its confirmation message
python -m code.main --phase init
# (the output must contain the line: Initialization complete)
```

## Important Note

The quickstart does **not** run any heavy model loading or GPU‑dependent
steps; it only verifies that the skeleton, dependencies, and dataset
streaming are functional on a CPU‑only GitHub Actions runner.

Later pipeline stages (data download, correlation analysis, clustering,
router inference, evaluation) are invoked by their own scripts and are
documented in the respective task specifications; run them after this
initialization step.

---
