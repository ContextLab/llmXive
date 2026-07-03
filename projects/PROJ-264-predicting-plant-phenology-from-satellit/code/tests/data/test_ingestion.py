"""
Unit tests for ingestion logic (mocked).
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.ingestion import get_cloud_free_sites

def test_get_cloud_free_sites_filtering():
    config = {
        "study_sites": [
            {"id": "site_1", "name": "Site A"},
            {"id": "site_2", "name": "Site B"},
            {"id": "site_3", "name": "Site C"}
        ],
        "selected_site_ids": ["site_1", "site_3"]
    }
    
    sites = get_cloud_free_sites(config)
    ids = [s["id"] for s in sites]
    
    assert "site_1" in ids
    assert "site_3" in ids
    assert "site_2" not in ids
    assert len(sites) == 2

def test_get_cloud_free_sites_empty_selection():
    config = {
        "study_sites": [
            {"id": "site_1", "name": "Site A"}
        ],
        "selected_site_ids": []
    }
    
    sites = get_cloud_free_sites(config)
    # Should fall back to all sites
    assert len(sites) == 1
    assert sites[0]["id"] == "site_1"