import pathlib

def test_spec_fr001_allows_both_modes():
    """
    Verify that the amended specification FR-001 explicitly allows
    filtering for both `diffusion_mode == "self"` and `diffusion_mode == "solute"`.
    """
    spec_path = pathlib.Path(__file__).parent.parent / "specs" / "001-predict-alloy-diffusion-on-the" / "spec.md"
    content = spec_path.read_text(encoding="utf-8")
    # Check that the FR-001 amendment text is present
    assert 'diffusion_mode == "self"' in content, "FR-001 must mention self diffusion mode"
    assert 'diffusion_mode == "solute"' in content, "FR-001 must mention solute diffusion mode"
    # Ensure the wording about allowing both modes exists
    expected_phrase = "both `diffusion_mode == \"self\"` and `diffusion_mode == \"solute\"`"
    assert expected_phrase in content, "FR-001 amendment should state both modes are allowed"