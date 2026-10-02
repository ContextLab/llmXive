"""
Integration test for task T200.

The test invokes the descriptor‑generation script and asserts that the
expected CSV file is created and contains at least one row (real data is
required – the test will fail loudly if the upstream download step has not
been performed).
"""
import os
import pathlib

import pytest

# The script under test
from generate_processed_descriptors import main as generate_main

@pytest.mark.integration
def test_descriptor_file_is_created(tmp_path: pathlib.Path):
    # Ensure a clean environment – the script writes to the project‑relative
    # ``data/processed`` directory, so we temporarily change cwd.
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Create the expected parent directories (the script does this itself,
        # but we guarantee they exist for the test runner).
        os.makedirs(os.path.join("data", "processed"), exist_ok=True)

        # Run the generation script
        generate_main()

        # Verify the output file exists
        output_path = pathlib.Path("data/processed/hea_descriptors.csv")
        assert output_path.is_file(), "Descriptor CSV was not created"

        # Load and perform a minimal sanity check
        import pandas as pd

        df = pd.read_csv(output_path)
        assert not df.empty, "Descriptor CSV is empty"
    finally:
        os.chdir(cwd)
