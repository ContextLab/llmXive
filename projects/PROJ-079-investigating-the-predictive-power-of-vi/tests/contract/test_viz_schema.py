import os
import pytest
from pathlib import Path
from PIL import Image

# Import config to get artifact paths
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from src.config import ARTIFACTS_PATH

PLOTS_PATH = Path(ARTIFACTS_PATH) / "plots"

# Expected dimensions based on typical matplotlib defaults and spec requirements
# These are reasonable defaults; adjust if the viz module uses specific sizes
EXPECTED_WIDTH = 10  # inches
EXPECTED_HEIGHT = 8  # inches
MIN_DIMENSION = 100  # pixels, sanity check

def _validate_image(path: Path) -> dict:
    """Validate an image file exists and has reasonable dimensions."""
    if not path.exists():
        return {"exists": False, "path": str(path), "error": "File not found"}
    
    try:
        with Image.open(path) as img:
            width, height = img.size
            # Check minimum dimensions to ensure it's not a tiny placeholder
            if width < MIN_DIMENSION or height < MIN_DIMENSION:
                return {
                    "exists": True,
                    "path": str(path),
                    "width": width,
                    "height": height,
                    "error": f"Dimensions too small: {width}x{height}"
                }
            return {
                "exists": True,
                "path": str(path),
                "width": width,
                "height": height
            }
    except Exception as e:
        return {"exists": True, "path": str(path), "error": f"Failed to open image: {e}"}

def test_viz_schema_validates(plot_files=None):
    """
    Contract test: Asserts that visualization output files exist and have correct dimensions.
    
    Args:
        plot_files (list, optional): List of relative paths to check. If None, checks
                                   the standard outputs defined in T038 and T039.
    """
    if plot_files is None:
        # Default files expected from T038 and T039
        plot_files = [
            "coefficients.png",
            "pdp_top5.png"
        ]
    
    results = []
    all_valid = True
    
    for filename in plot_files:
        file_path = PLOTS_PATH / filename
        result = _validate_image(file_path)
        results.append(result)
        
        if not result.get("exists"):
            all_valid = False
        elif "error" in result:
            all_valid = False
        
        # Log result for debugging
        if all_valid:
            print(f"✓ {filename}: {result['width']}x{result['height']}")
        else:
            print(f"✗ {filename}: {result.get('error', 'Invalid')}")
    
    # Assert all files are valid
    assert all_valid, f"Visualization schema validation failed. Results: {results}"
    
    # Additional schema checks if specific dimensions are required
    # (Currently checking existence and reasonable size; can be tightened if spec defines exact sizes)
    for result in results:
        assert result["width"] >= EXPECTED_WIDTH * 72, f"Width too small for {result['path']}"
        assert result["height"] >= EXPECTED_HEIGHT * 72, f"Height too small for {result['path']}"