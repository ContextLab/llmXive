"""
Integration test for the full analysis pipeline (scoring -> degradation -> statistical test).
"""
import sys
import json
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

def test_import_analysis_modules():
    """Verify all analysis modules can be imported."""
    from analysis.scoring import score_images
    from analysis.compute_degradation import compute_degradation
    from analysis.calculate_gap import calculate_gap
    from analysis.statistical_test import run_statistical_test
    
    assert callable(score_images)
    assert callable(compute_degradation)
    assert callable(calculate_gap)
    assert callable(run_statistical_test)