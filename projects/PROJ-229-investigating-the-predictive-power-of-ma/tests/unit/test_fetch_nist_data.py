"""
Unit tests for fetch_nist_data.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from code.data.fetch_nist_data import (
    fetch_nist_data,
    load_materials_project_data,
    calculate_overlap,
    update_target_decision,
    save_nist_data,
    main,
    FALLBACK_THRESHOLD
)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    data_dir = tmp_path / "data" / "raw"
    results_dir = tmp_path / "data" / "results"
    data_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    
    # Patch the global constants to use temp paths
    with patch("code.data.fetch_nist_data.DATA_DIR", data_dir), \
         patch("code.data.fetch_nist_data.RESULTS_DIR", results_dir), \
         patch("code.data.fetch_nist_data.NIST_OUTPUT_PATH", data_dir / "nist_data.json"), \
         patch("code.data.fetch_nist_data.TARGET_DECISION_PATH", results_dir / "target_decision.json"):
        yield data_dir, results_dir


def test_fetch_nist_data_success(temp_data_dir):
    """Test successful fetch of NIST data."""
    mock_data = [{"material_id": "mp-123", "property": 1.0}, {"material_id": "mp-456", "property": 2.0}]
    
    with patch("code.data.fetch_nist_data.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        df = fetch_nist_data()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "material_id" in df.columns
        assert df.iloc[0]["material_id"] == "mp-123"


def test_fetch_nist_data_empty(temp_data_dir):
    """Test fetch returning empty data."""
    with patch("code.data.fetch_nist_data.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        df = fetch_nist_data()
        
        assert df.empty


def test_fetch_nist_data_failure(temp_data_dir):
    """Test fetch failing due to network error."""
    with patch("code.data.fetch_nist_data.requests.get") as mock_get:
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(RuntimeError, match="Failed to fetch NIST data"):
            fetch_nist_data()


def test_calculate_overlap():
    """Test overlap calculation logic."""
    nist_df = pd.DataFrame({"material_id": ["mp-1", "mp-2", "mp-3"]})
    mp_df = pd.DataFrame({"material_id": ["mp-2", "mp-3", "mp-4"]})
    
    overlap = calculate_overlap(nist_df, mp_df)
    assert overlap == 2
    
    # Test empty overlap
    mp_df_empty = pd.DataFrame({"material_id": ["mp-5"]})
    overlap_empty = calculate_overlap(nist_df, mp_df_empty)
    assert overlap_empty == 0
    
    # Test missing columns
    nist_no_id = pd.DataFrame({"other": ["a"]})
    overlap_missing = calculate_overlap(nist_no_id, mp_df)
    assert overlap_missing == 0


def test_update_target_decision_fallback(temp_data_dir):
    """Test updating target_decision.json with fallback flag."""
    data_dir, results_dir = temp_data_dir
    
    update_target_decision(fallback=True, reason="Low overlap")
    
    decision_path = results_dir / "target_decision.json"
    assert decision_path.exists()
    
    with open(decision_path, "r") as f:
        decision = json.load(f)
    
    assert decision["status"] == "fallback"
    assert decision["target"] == "melting_point"
    assert decision["reason"] == "Low overlap"


def test_update_target_decision_no_fallback(temp_data_dir):
    """Test updating target_decision.json without fallback flag."""
    data_dir, results_dir = temp_data_dir
    
    update_target_decision(fallback=False, reason="Sufficient overlap")
    
    decision_path = results_dir / "target_decision.json"
    assert decision_path.exists()
    
    with open(decision_path, "r") as f:
        decision = json.load(f)
    
    assert decision["status"] == "confirmed"
    assert decision["target"] == "latent_heat"


def test_main_low_overlap(temp_data_dir):
    """Test main function triggers fallback when overlap < 500."""
    data_dir, results_dir = temp_data_dir
    
    # Mock NIST fetch
    mock_nist_data = [{"material_id": f"mp-{i}"} for i in range(100)]
    
    # Mock MP data with small overlap
    mock_mp_data = [{"material_id": f"mp-{i}"} for i in range(50)]
    mp_file = data_dir / "materials_project_data.json"
    with open(mp_file, "w") as f:
        json.dump(mock_mp_data, f)
    
    with patch("code.data.fetch_nist_data.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_nist_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        main()
        
        # Check that fallback was triggered
        decision_path = results_dir / "target_decision.json"
        with open(decision_path, "r") as f:
            decision = json.load(f)
        
        assert decision["status"] == "fallback"
        assert "overlap" in decision["reason"].lower()
        
        # Check NIST data was saved
        nist_file = data_dir / "nist_data.json"
        assert nist_file.exists()


def test_main_high_overlap(temp_data_dir):
    """Test main function does not trigger fallback when overlap >= 500."""
    data_dir, results_dir = temp_data_dir
    
    # Mock NIST fetch with 600 entries
    mock_nist_data = [{"material_id": f"mp-{i}"} for i in range(600)]
    
    # Mock MP data with high overlap
    mock_mp_data = [{"material_id": f"mp-{i}"} for i in range(600)]
    mp_file = data_dir / "materials_project_data.json"
    with open(mp_file, "w") as f:
        json.dump(mock_mp_data, f)
    
    with patch("code.data.fetch_nist_data.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_nist_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        main()
        
        # Check that no fallback was triggered
        decision_path = results_dir / "target_decision.json"
        with open(decision_path, "r") as f:
            decision = json.load(f)
        
        assert decision["status"] == "confirmed"