"""Contract test that verifies the required data sub‑directories exist and
contain at least one file each."""
import pathlib

def test_data_hierarchy_exists_and_nonempty():
    base = pathlib.Path(__file__).parents[2] / "data"
    expected = {"raw", "processed", "aggregated"}
    actual_dirs = {p.name for p in base.iterdir() if p.is_dir()}
    assert expected == actual_dirs, f"Expected {expected}, found {actual_dirs}"

    # Verify each required sub‑directory contains at least one file.
    for sub in expected:
        sub_path = base / sub
        files = [p for p in sub_path.iterdir() if p.is_file()]
        assert files, f"Directory '{sub}' should contain at least one file"