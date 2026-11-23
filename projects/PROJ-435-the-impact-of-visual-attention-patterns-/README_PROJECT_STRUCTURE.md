# Project Structure Verification (Task T001)

This document confirms the creation of the project directory structure as per the implementation plan.

## Required Directories

The following directories have been created relative to the project root:

- `code/` - Source code for the pipeline
- `data/raw/` - Raw input data (downloaded from external sources)
- `data/derived/` - Intermediate processed data
- `data/processed/` - Final clean datasets ready for analysis
- `tests/` - Test suites (contract, integration, unit)
- `state/` - Runtime state, checksums, and logs

## Verification

Run the following command to verify the structure:

```bash
python code/setup_data_structure.py
```

Or run the tests:

```bash
pytest tests/test_project_structure.py -v
```

## Notes

- All paths are relative to the project root.
- The `data/` directory is subdivided into `raw`, `derived`, and `processed` to maintain data lineage.
- The `state/` directory is used for reproducibility artifacts (checksums, random seeds, runtime events).