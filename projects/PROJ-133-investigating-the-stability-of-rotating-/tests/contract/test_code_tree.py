"""Contract test that verifies the required code sub‑directories exist."""
import pathlib

def test_code_tree():
    base = pathlib.Path(__file__).parents[2] / "code"
    expected = {"simulation", "analysis", "statistics", "viz", "utils"}
    actual = {p.name for p in base.iterdir() if p.is_dir()}
    assert expected == actual, f"Expected {expected}, found {actual}"
