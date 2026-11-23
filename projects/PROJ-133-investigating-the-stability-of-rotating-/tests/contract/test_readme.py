"""Contract test that validates the presence of a quick‑start command in README."""
import pathlib

def test_readme_contains_quickstart():
    readme_path = pathlib.Path(__file__).parents[2] / "README.md"
    assert readme_path.is_file(), "README.md not found"
    content = readme_path.read_text(encoding="utf-8")
    assert "python -m simulation.runner" in content, "Quick‑start command missing"
