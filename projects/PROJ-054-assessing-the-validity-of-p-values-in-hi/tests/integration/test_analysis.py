import pytest
import json
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

def test_full_analysis_pipeline():
    """Test the full analysis pipeline if data exists."""
    base_dir = Path(__file__).parent.parent.parent
    ks_stats_path = base_dir / 'data' / 'results' / 'ks_stats.json'
    
    if not ks_stats_path.exists():
        pytest.skip("KS stats file not found. Run the pipeline first.")
    
    with open(ks_stats_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) > 0
    assert 'ks_statistic' in data[0]
    assert 'permutation_pvalues' in data[0]
    assert 'standard_pvalues' in data[0]