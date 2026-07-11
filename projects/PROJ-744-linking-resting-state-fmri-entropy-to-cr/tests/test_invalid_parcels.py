import os
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.entropy import flag_invalid_parcels

def test_flag_invalid_parcels_below_threshold():
    """Test that subjects with <10% invalid parcels are NOT flagged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create 360 parcels, 10 invalid (2.7%)
        results = {f"parcel_{i}": np.nan if i < 10 else 0.5 for i in range(360)}
        flagged = flag_invalid_parcels("sub_test", results, threshold=0.10, log_dir=tmpdir)
        
        assert flagged is False, "Subject should not be flagged when invalid ratio < 10%"
        
        # Check log file does not exist or has no entry for this subject
        log_path = Path(tmpdir) / "invalid_parcels.log"
        if log_path.exists():
            with open(log_path) as f:
                content = f.read()
            assert "sub_test" not in content, "Log should not contain entry for non-flagged subject"

def test_flag_invalid_parcels_above_threshold():
    """Test that subjects with >10% invalid parcels ARE flagged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create 360 parcels, 50 invalid (13.8%)
        results = {f"parcel_{i}": np.nan if i < 50 else 0.5 for i in range(360)}
        flagged = flag_invalid_parcels("sub_flagged", results, threshold=0.10, log_dir=tmpdir)
        
        assert flagged is True, "Subject should be flagged when invalid ratio > 10%"
        
        # Check log file exists and contains entry
        log_path = Path(tmpdir) / "invalid_parcels.log"
        assert log_path.exists(), "Log file should be created"
        
        with open(log_path) as f:
            content = f.read()
        assert "sub_flagged" in content, "Log should contain entry for flagged subject"
        assert "13.88%" in content or "14" in content, "Log should contain percentage info"

def test_flag_invalid_parcels_exact_threshold():
    """Test boundary condition: exactly 10% invalid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create 100 parcels, 10 invalid (10%)
        # Condition is > 10%, so 10% exactly should NOT flag
        results = {f"parcel_{i}": np.nan if i < 10 else 0.5 for i in range(100)}
        flagged = flag_invalid_parcels("sub_boundary", results, threshold=0.10, log_dir=tmpdir)
        
        assert flagged is False, "Subject should not be flagged at exactly 10% (condition is > 10%)"
        
        log_path = Path(tmpdir) / "invalid_parcels.log"
        if log_path.exists():
            with open(log_path) as f:
                content = f.read()
            assert "sub_boundary" not in content

def test_flag_invalid_parcels_all_invalid():
    """Test subject with 100% invalid parcels."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results = {f"parcel_{i}": np.nan for i in range(360)}
        flagged = flag_invalid_parcels("sub_all_nan", results, threshold=0.10, log_dir=tmpdir)
        
        assert flagged is True, "Subject with all NaN should be flagged"
        
        log_path = Path(tmpdir) / "invalid_parcels.log"
        assert log_path.exists()
        with open(log_path) as f:
            content = f.read()
        assert "sub_all_nan" in content