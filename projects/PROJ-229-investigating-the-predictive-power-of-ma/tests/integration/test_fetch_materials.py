"""
Integration test for task T005a.

The test runs the fetch script and verifies that the expected output
file `data/raw/materials_project_data.json` is created.
"""

import pathlib
import importlib

def test_fetch_materials_creates_output():
    """
    Execute the fetch pipeline and assert the output JSON file exists.
    """
    # Ensure the output directory exists
    raw_dir = pathlib.Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    output_file = raw_dir / "materials_project_data.json"

    # Remove any pre-existing file to guarantee the test checks creation
    if output_file.is_file():
        output_file.unlink()

    # Import and run the main function from the fetch module
    fetch_module = importlib.import_module("data.fetch_materials")
    fetch_main = getattr(fetch_module, "main")
    fetch_main()

    # After execution the file must exist
    assert output_file.is_file(), (
        f"Expected output file {output_file} was not created by fetch_materials.main()"
    )