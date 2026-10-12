"""Contract test that verifies the required data sub‑directories exist."""
import pathlib

def test_data_tree():
    base = pathlib.Path(__file__).parents[2] / "data"
    expected = {"raw", "processed", "aggregated"}
    actual = {p.name for p in base.iterdir() if p.is_dir()}
    assert expected == actual, f"Expected {expected}, found {actual}"
