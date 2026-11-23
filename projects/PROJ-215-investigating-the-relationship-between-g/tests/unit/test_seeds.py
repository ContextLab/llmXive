"""
Unit test for the ``code/seeds.py`` script.

The test ensures that:
  1. Running the script creates the expected YAML file under
     ``data/state/seeds.yaml``.
  2. The file contains the required integer entries:
     ``random_seed``, ``numpy_seed`` and optionally ``torch_seed``.
  3. All present seed values are integers.
"""

import os
from pathlib import Path

import yaml

# Import the module under test. Importing should not raise any errors.
import importlib.util

# Load the seeds module from its path.
seeds_path = Path(__file__).resolve().parents[2] / "code" / "seeds.py"
spec = importlib.util.spec_from_file_location("seeds", seeds_path)
seeds = importlib.util.module_from_spec(spec)  # type: ignore
assert spec is not None
spec.loader.exec_module(seeds)  # type: ignore

def test_generate_seeds_yaml_creates_file(tmp_path):
    """
    Execute the ``generate_seeds_yaml`` function and verify the output file.
    """
    # Ensure a clean environment: remove any pre‑existing file.
    output_file = Path(seeds_path.parent.parent, "data", "state", "seeds.yaml")
    if output_file.exists():
        output_file.unlink()

    # Run the function – it should create the file.
    created_path = seeds.generate_seeds_yaml()
    assert created_path == output_file
    assert created_path.is_file(), "Seed file was not created"

    # Load the YAML and check required keys.
    with created_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Required keys
    required_keys = {"random_seed", "numpy_seed"}
    assert required_keys.issubset(data.keys()), f"Missing required keys: {required_keys - data.keys()}"

    # All present values must be integers.
    for key, value in data.items():
        assert isinstance(value, int), f"Seed value for {key} is not an integer"

    # Clean up after test.
    created_path.unlink()
    # Remove the intermediate directory if empty.
    try:
        created_path.parent.rmdir()
    except OSError:
        pass

# Execute the test when the module is run directly (useful for quick sanity check).
if __name__ == "__main__":
    test_generate_seeds_yaml_creates_file(None)