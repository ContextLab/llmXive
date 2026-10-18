# Quickstart: Project Skeleton Initialization

This guide explains how to set up the project skeleton and verify that the
basic configuration is working.

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
- All required sub‑directories under `code/` (analysis, models, quantization,
  evaluation, utils, data, runners, validation, security) have been created,
  each with an `__init__.py` package marker.
- The `tests/` directory is in place.
- The `data/raw`, `data/processed` (with `logs/`, `activation_stats/`,
  `rotation_matrices/`, `generated_images/`) and `figures/` directories are
  also in place.

Note: the entry point uses `parse_known_args`, so piping its output
(e.g. `python -m code.main --phase init | grep "Initialization complete"`)
works both in a shell and when the pipe fragment is passed as literal
arguments by a non‑shell runner.

## Verification

You can run a few quick checks to confirm the setup:

```bash
# Count the number of sub‑directories under code/
find code/ -type d | wc -l   # should be ≥ 8

# Ensure the config module imports without error
python -c "import code.config"

# Verify that the requirements file lists torch
grep -c "torch" requirements.txt   # should be ≥ 1

# Confirm the init phase prints its confirmation message
python -m code.main --phase init | grep "Initialization complete"
```

Once these checks pass, the project skeleton is ready for further
development and data acquisition steps (see `code/data/download_coco.py`
and `code/data/download_diverse_prompts.py` in the next task).