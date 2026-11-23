# Dummy Data Directory

This directory is intended for dummy/placeholder data used in integration tests (e.g., T011).
The `tests/integration/test_pipeline.py` script will generate its own dummy data
dynamically in a temporary directory to ensure isolation and reproducibility.

Do not place permanent data here. The test creates a `data/dummy` structure
inside a temporary folder, populates it with synthetic MNE RawArray objects,
runs the pipeline, and then cleans up.

If you need to run the test manually, ensure the `tests/integration/test_pipeline.py`
script is executed, which handles the data generation.