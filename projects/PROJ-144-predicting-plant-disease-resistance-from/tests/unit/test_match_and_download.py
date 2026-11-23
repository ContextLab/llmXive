import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.match_and_download import (
    DataAvailabilityError,
    load_manifest,
    has_resistance_metadata,
    has_temporal_metadata,
    check_metadata_in_preview,
    RESISTANCE_COLUMNS,
    TEMPORAL_COLUMNS
)

def test_load_manifest_missing():
    """Test that load_manifest raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_manifest(Path("non_existent_file.json"))

def test_has_resistance_metadata():
    """Test resistance metadata detection."""
    # Should return True if any resistance column is present
    assert has_resistance_metadata({'phenotype', 'other_col'}) is True
    assert has_resistance_metadata({'resistance_score', 'timepoint'}) is True
    assert has_resistance_metadata({'disease_status'}) is True
    assert has_resistance_metadata({'challenge_outcome'}) is True
    
    # Should return False if no resistance columns
    assert has_resistance_metadata({'sample_id', 'timepoint'}) is False
    assert has_resistance_metadata(set()) is False

def test_has_temporal_metadata():
    """Test temporal metadata detection."""
    # Should return True if any temporal column is present
    assert has_temporal_metadata({'timepoint', 'other_col'}) is True
    assert has_temporal_metadata({'sample_date', 'resistance_score'}) is True
    assert has_temporal_metadata({'inoculation_date'}) is True
    assert has_temporal_metadata({'days_post_inoculation'}) is True
    
    # Should return False if no temporal columns
    assert has_temporal_metadata({'sample_id', 'resistance_score'}) is False
    assert has_temporal_metadata(set()) is False

def test_check_metadata_in_preview():
    """Test the generic metadata check function."""
    assert check_metadata_in_preview({'a', 'b'}, {'a'}) is True
    assert check_metadata_in_preview({'a', 'b'}, {'c'}) is False
    assert check_metadata_in_preview(set(), {'a'}) is False
    assert check_metadata_in_preview(None, {'a'}) is False

def test_data_availability_error():
    """Test that DataAvailabilityError is a custom exception."""
    try:
        raise DataAvailabilityError("No data found")
    except DataAvailabilityError as e:
        assert str(e) == "No data found"
    except Exception:
        pytest.fail("DataAvailabilityError not raised correctly")
