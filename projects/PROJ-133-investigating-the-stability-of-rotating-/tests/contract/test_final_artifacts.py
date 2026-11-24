"""Contract test for final artifacts."""
import pathlib

def test_final_artifacts():
    json_path = pathlib.Path(__file__).parents[2] / "data" / "aggregated" / "final_phase_diagram.json"
    png_path = pathlib.Path(__file__).parents[2] / "figures" / "final_phase_diagram.png"
    md_path = pathlib.Path(__file__).parents[2] / "docs" / "methods.md"
    assert json_path.is_file(), "final_phase_diagram.json missing"
    assert png_path.is_file(), "final_phase_diagram.png missing"
    assert md_path.is_file(), "methods.md missing"
    # Simple check that methods.md contains at least one citation.
    content = md_path.read_text(encoding="utf-8")
    assert "[" in content and "]" in content, "methods.md lacks citations"
