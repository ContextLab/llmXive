# Quickstart Guide: llmXive Pipeline Validation

This document provides instructions for validating the end-to-end llmXive automated science pipeline on a CPU-only runner.

## Prerequisites

- Python 3.9+
- Installed dependencies (see `requirements.txt`)
- Project root directory

## Validation Steps

The pipeline validation is performed by the script `code/validation/quickstart_validator.py`.

### 1. Verify Project Structure

Ensure the following directories and files exist:
- `code/`, `data/`, `tests/`, `specs/`
- `data/raw/.checksums.txt`
- `data/processed/scheduler_trace.json`

### 2. Run the Validator

Execute the validation script from the project root:

```bash
python code/validation/quickstart_validator.py
```

This script will:
1. Check for required directories and files.
2. Run the `CurriculumScheduler` with mock data to ensure logic integrity.
3. Execute the `Convergence`, `Sensitivity`, and `Transfer` analysis modules.
4. Verify that output artifacts are generated or present.

### 3. Expected Output

Upon successful validation, you should see:
- `✓` markers for all checks.
- A summary message: "All validation checks passed."
- No tracebacks or errors.

## Troubleshooting

- **Missing Files**: If the validator reports missing files (e.g., `coverage_vectors.json`), ensure that the prerequisite tasks (T001-T046) have been completed and their artifacts generated.
- **Import Errors**: Ensure `code/` is in your `PYTHONPATH` or run from the project root.
- **CPU Constraints**: The validator uses CPU-optimized configurations. If you encounter memory issues, reduce the mock data size in the script.

## Next Steps

Once validated, you can proceed to run the full training pipeline with real data by executing `code/training/runner.py`.
