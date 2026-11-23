import pathlib

def test_spec_contains_solute_mode():
    """
    Verify that the amended specification (spec.md) explicitly mentions
    the allowance for `diffusion_mode == "solute"` as required by FR-001.
    """
    # Locate the project root (two levels up from this test file)
    project_root = pathlib.Path(__file__).resolve().parents[3]
    spec_path = project_root / "specs" / "001-predicting-the-impact-of-alloying-on-the" / "spec.md"
    content = spec_path.read_text(encoding="utf-8")
    assert 'diffusion_mode == "solute"' in content, "Spec amendment missing solute diffusion mode clause"
    # Also check that the acceptance scenario mentions both self and solute
    assert "or `diffusion_mode == \"solute\"`" in content, "Acceptance scenario does not reflect dual-mode requirement"