"""
Basic scaffolding test to ensure the code module structure is importable.
"""

import pytest
import sys
from pathlib import Path

# Ensure the project root is in the path for imports
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def test_code_package_exists():
    """Verify the code package root exists and is importable."""
    try:
        import code
        assert hasattr(code, '__version__')
    except ImportError as e:
        pytest.fail(f"Failed to import code package: {e}")

def test_scoring_module_exists():
    """Verify the scoring submodule exists."""
    try:
        import code.scoring
        assert hasattr(code.scoring, '__name__')
    except ImportError as e:
        pytest.fail(f"Failed to import code.scoring: {e}")

def test_analysis_module_exists():
    """Verify the analysis submodule exists."""
    try:
        import code.analysis
        assert hasattr(code.analysis, '__name__')
    except ImportError as e:
        pytest.fail(f"Failed to import code.analysis: {e}")

def test_validation_module_exists():
    """Verify the validation submodule exists."""
    try:
        import code.validation
        assert hasattr(code.validation, '__name__')
    except ImportError as e:
        pytest.fail(f"Failed to import code.validation: {e}")

def test_viz_module_exists():
    """Verify the viz submodule exists."""
    try:
        import code.viz
        assert hasattr(code.viz, '__name__')
    except ImportError as e:
        pytest.fail(f"Failed to import code.viz: {e}")