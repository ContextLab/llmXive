"""
Integration test for single-prompt generation on CPU.
"""
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

def test_import_inference_module():
    """Verify the inference module can be imported."""
    from inference.inference import load_model, generate_image
    assert callable(load_model)
    assert callable(generate_image)


def test_import_pilot_generation():
    """Verify the pilot generation module can be imported."""
    from inference.generate_pilot import generate_pilot_images
    assert callable(generate_pilot_images)
