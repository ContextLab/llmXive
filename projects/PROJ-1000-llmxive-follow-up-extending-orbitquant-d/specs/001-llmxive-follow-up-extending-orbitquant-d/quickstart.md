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
- All required sub-directories under `code/` (analysis, models, quantization,
  evaluation, utils, data, runners, validation, security) have been created,
  each with an `__init__.py` package marker.
- The `tests/` directory is in place (with a placeholder test).
- The `data/raw`, `data/processed` (with `logs/`, `activation_stats/`,
  `rotation_matrices/`, `generated_images/`) and `figures/` directories are
  also in place.

## Verify Dataset Access

The pipeline relies on the HuggingFace `coco2017` dataset, which includes
both images and captions. Run the following snippet to confirm it can be
streamed without manual download:

```python
from datasets import load_dataset

ds = load_dataset('coco2017', split='validation', streaming=True)
first = next(iter(ds))
print(f"Image URL: {first['image']}  Caption: {first['caption']}")
```

If the script prints a valid image URL and a caption, the dataset is
reachable.

## Verification

You can run a few quick checks to confirm the setup:

```bash
# Count the number of sub-directories under code/
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

The quickstart does **not** run any heavy model loading or GPU-dependent
steps; it only verifies that the skeleton, dependencies, and dataset
streaming are functional on a CPU-only GitHub Actions runner.

Later pipeline stages (data download, correlation analysis, clustering,
router inference, evaluation) are invoked by their own scripts and are
documented in the respective task specifications; run them after this
initialization step.
