"""
Integration test to verify the vignette engine runs and produces output files.
This ensures the test suite can actually execute against the implementation.
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vignette_engine import generate_vignettes


def test_vignette_engine_executes_successfully():
    """Verify the vignette engine can be executed without errors."""
    try:
        result = generate_vignettes()
        assert isinstance(result, dict), "Result must be a dictionary"
        assert len(result) == 3, "Result must contain exactly 3 conditions"
        assert all(key in result for key in ["battle", "journey", "medical"]), \
            "Result must contain battle, journey, and medical keys"
    except Exception as e:
        pytest.fail(f"Vignette engine execution failed: {e}")

def test_vignette_engine_output_structure():
    """Verify the structure of the vignette engine output."""
    result = generate_vignettes()
    
    for condition, text in result.items():
        assert isinstance(text, str), f"{condition} text must be a string"
        assert len(text) > 0, f"{condition} text must not be empty"
        assert "Alex" in text, f"{condition} text must mention the protagonist"
        assert "two years" in text, f"{condition} text must mention duration"