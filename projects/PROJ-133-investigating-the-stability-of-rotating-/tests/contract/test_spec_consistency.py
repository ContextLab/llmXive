"""Contract test that ensures the spec mentions Two‑Way ANOVA and Vortex Density."""
import pathlib

def test_spec_mentions_two_way_anova_and_vortex_density():
    spec_path = pathlib.Path(__file__).parents[2] / "specs" / "001-investigating-the-stability-of-rotating" / "spec.md"
    assert spec_path.is_file(), "spec.md not found"
    content = spec_path.read_text(encoding="utf-8")
    assert "Two‑Way ANOVA" in content, "Two‑Way ANOVA not mentioned in spec"
    assert "Vortex Density" in content, "Vortex Density not mentioned in spec"
