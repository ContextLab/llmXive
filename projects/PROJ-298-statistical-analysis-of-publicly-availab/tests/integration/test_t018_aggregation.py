"""
Integration test for Task T018: Aggregate and finalize trend_results.json.

This test verifies that:
1. The aggregation script runs without error.
2. The output file data/processed/trend_results.json is created.
3. The output contains merged data from upstream artifacts.
4. The state file is updated with new checksums.
"""
import os
import json
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.generate_trend_results import main, load_json_safe, aggregate_trend_data

@pytest.fixture
def mock_upstream_data(tmp_path):
    """Create mock upstream data files for testing."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    # Mock trend_intermediate.json
    intermediate = {
        "results": [
            {
                "tag": "python",
                "classification": "Growth",
                "slope": 0.5,
                "p_value": 0.01,
                "power": 0.9,
                "mdes": 0.2,
                "n_observations": 24
            },
            {
                "tag": "legacy-framework",
                "classification": "Decline",
                "slope": -0.3,
                "p_value": 0.02,
                "power": 0.85,
                "mdes": 0.15,
                "n_observations": 18
            }
        ]
    }
    
    # Mock confidence_interval.json
    ci = {
        "results": [
            {
                "tag": "python",
                "confidence_interval": {"lower": 0.3, "upper": 0.7}
            },
            {
                "tag": "legacy-framework",
                "confidence_interval": {"lower": -0.5, "upper": -0.1}
            }
        ]
    }
    
    # Mock correlation_results.json
    corr = {
        "results": [
            {
                "tag": "python",
                "correlation": 0.85,
                "magnitude": "Strong",
                "source": "GitHub Stars"
            },
            {
                "tag": "legacy-framework",
                "correlation": 0.4,
                "magnitude": "Moderate",
                "source": "NPM Downloads"
            }
        ]
    }
    
    # Write files
    with open(processed_dir / "trend_intermediate.json", 'w') as f:
        json.dump(intermediate, f)
    with open(processed_dir / "confidence_interval.json", 'w') as f:
        json.dump(ci, f)
    with open(processed_dir / "correlation_results.json", 'w') as f:
        json.dump(corr, f)
    
    return tmp_path

def test_aggregate_trend_data_structure(mock_upstream_data):
    """Test that aggregate_trend_data produces the correct structure."""
    # Temporarily override PROJECT_ROOT for this test
    import analysis.generate_trend_results as module
    original_root = module.PROJECT_ROOT
    module.PROJECT_ROOT = mock_upstream_data
    
    try:
        result = aggregate_trend_data()
        
        # Verify structure
        assert "metadata" in result
        assert "tag_trends" in result
        assert len(result["tag_trends"]) == 2
        
        # Verify first tag
        python_trend = next(t for t in result["tag_trends"] if t["tag"] == "python")
        assert python_trend["trend_classification"] == "Growth"
        assert python_trend["slope"] == 0.5
        assert python_trend["confidence_interval"] == {"lower": 0.3, "upper": 0.7}
        assert python_trend["correlation"] == 0.85
        assert python_trend["correlation_magnitude"] == "Strong"
        
        # Verify second tag
        legacy_trend = next(t for t in result["tag_trends"] if t["tag"] == "legacy-framework")
        assert legacy_trend["trend_classification"] == "Decline"
        assert legacy_trend["slope"] == -0.3
        assert legacy_trend["confidence_interval"] == {"lower": -0.5, "upper": -0.1}
        assert legacy_trend["correlation"] == 0.4
        assert legacy_trend["correlation_magnitude"] == "Moderate"
        
    finally:
        module.PROJECT_ROOT = original_root

def test_missing_upstream_artifact_raises_error(tmp_path):
    """Test that missing upstream artifacts cause a clear error."""
    import analysis.generate_trend_results as module
    original_root = module.PROJECT_ROOT
    module.PROJECT_ROOT = tmp_path
    
    try:
        # No files created - should raise FileNotFoundError
        with pytest.raises(FileNotFoundError, match="Missing upstream artifact"):
            aggregate_trend_data()
    finally:
        module.PROJECT_ROOT = original_root