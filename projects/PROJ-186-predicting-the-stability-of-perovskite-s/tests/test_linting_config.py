"""
Test to verify that linting and formatting configurations exist and are valid.
This ensures T003 is properly implemented.
"""
import os
import toml

def test_ruff_config_exists():
    """Verify .ruff.toml exists in the code directory."""
    code_dir = os.path.join(os.path.dirname(__file__), "..", "code")
    ruff_path = os.path.join(code_dir, ".ruff.toml")
    assert os.path.exists(ruff_path), f"Ruff config not found at {ruff_path}"

    # Verify it is valid TOML
    with open(ruff_path, "r") as f:
        try:
            toml.load(f)
        except Exception as e:
            raise AssertionError(f"Invalid TOML in .ruff.toml: {e}")

def test_black_config_exists():
    """Verify .black.toml exists in the code directory."""
    code_dir = os.path.join(os.path.dirname(__file__), "..", "code")
    black_path = os.path.join(code_dir, ".black.toml")
    assert os.path.exists(black_path), f"Black config not found at {black_path}"

    # Verify it is valid TOML
    with open(black_path, "r") as f:
        try:
            toml.load(f)
        except Exception as e:
            raise AssertionError(f"Invalid TOML in .black.toml: {e}")

def test_requirements_includes_linters():
    """Verify requirements.txt includes ruff and black."""
    root_dir = os.path.join(os.path.dirname(__file__), "..")
    req_path = os.path.join(root_dir, "requirements.txt")
    assert os.path.exists(req_path), "requirements.txt not found"

    with open(req_path, "r") as f:
        content = f.read().lower()
    
    assert "ruff" in content, "ruff not found in requirements.txt"
    assert "black" in content, "black not found in requirements.txt"