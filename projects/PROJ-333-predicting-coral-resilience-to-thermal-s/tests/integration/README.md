# Integration Tests for Coral Resilience Pipeline

This directory contains integration tests that verify the pipeline flow
using mock small FASTQ files. These tests are designed to run without
downloading real data from NCBI, ensuring they can be executed in CI/CD
environments with limited bandwidth or storage.

## Purpose

- Verify that the ingestion logic (checksum calculation, file handling) works.
- Verify that the logging and memory tracking infrastructure functions correctly.
- Verify that the configuration loading works as expected.
- Ensure the pipeline directory structure is created correctly.

## Mock Data

The tests use `conftest.py` to generate small, valid FASTQ and FASTQ.gz files
in memory or temporary files. These are sufficient to test the logic of:
- `calculate_checksum`
- `verify_file_integrity` (simulated)
- `setup_logger`
- `ensure_directories`

## Running the Tests

```bash
pytest tests/integration/ -v
```

## Dependencies

These tests rely on the core modules:
- `code/config.py`
- `code/utils/logging.py`
- `code/data/ingest.py`

Ensure these modules are correctly implemented before running these tests.
