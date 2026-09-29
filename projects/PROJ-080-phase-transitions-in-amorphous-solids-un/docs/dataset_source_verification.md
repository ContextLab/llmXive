# Dataset Source Verification Configuration

## Overview
This document describes the environment configuration and verification process for the `amorphous-silicon-shear-trajectories` dataset.

## Dataset Source
- **Repository**: `llmXive/amorphous-silicon-shear-trajectories`
- **Platform**: HuggingFace Datasets
- **Verification Method**: Programmatic integrity check via `datasets.load_dataset()`

## Environment Variables
The following environment variable must be set to enable strict dataset verification:

```bash
export HF_DATASET_VERIFY=1
```

If this variable is not set or not equal to "1", the pipeline will proceed but may issue warnings (depending on logging configuration).

## Verification Process
1. The `verify_source_integrity()` function in `code/env_config.py` is called.
2. It attempts to load the dataset in streaming mode to verify accessibility.
3. If successful, the dataset is considered verified.
4. If failed, a `RuntimeError` is raised, halting the pipeline.

## Usage in Pipeline
```python
from env_config import verify_source_integrity, load_verified_dataset

# Verify source before loading
if not verify_source_integrity("llmXive/amorphous-silicon-shear-trajectories"):
 raise RuntimeError("Dataset source verification failed")

# Load dataset
dataset = load_verified_dataset(streaming=True)
```

## Failure Handling
- If the dataset is unavailable, the pipeline halts with a clear error message.
- No synthetic or fallback data is generated.
- Logs are written to the configured logging system (see `logging_config.py`).

## Maintenance
- Update `DATASET_HF_REPO_ID` in `code/env_config.py` if the dataset repository changes.
- Ensure `requirements.txt` includes the `datasets` library.
- Run `pytest tests/unit/test_env_config.py` to verify configuration.