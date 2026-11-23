"""
Integration tests for the full data pipeline.
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.ingest import ingest_elastic_data
from src.data.clean import clean_elastic_data
from src.data.features import compute_compositional_features
from src.utils.logging import setup_logger

logger = setup_logger("test_pipeline", level=logging.DEBUG)

@pytest.fixture
def static_manifest():
    """Create a static manifest file with known FCC material IDs."""
    manifest = {
        "materials": [
            {"id": "MP-123", "element": "Al", "crystal_system": "fcc"},
            {"id": "MP-456", "element": "Cu", "crystal_system": "fcc"},
            {"id": "MP-789", "element": "Ni", "crystal_system": "fcc"},
            {"id": "MP-101", "element": "Ag", "crystal_system": "fcc"},
            {"id": "MP-102", "element": "Au", "crystal_system": "fcc"}
        ]
    }
    return manifest

@pytest.fixture
def temp_manifest_file(static_manifest):
    """Create a temporary manifest file."""
    import json
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(static_manifest, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = os.path.join(tmpdir, "raw")
        processed_dir = os.path.join(tmpdir, "processed")
        os.makedirs(raw_dir)
        os.makedirs(processed_dir)
        yield {
            "raw": raw_dir,
            "processed": processed_dir,
            "base": tmpdir
        }

def test_pipeline_end_to_end_static(temp_manifest_file, temp_data_dir):
    """Test the full pipeline end-to-end using a static manifest."""
    # Mock the API responses for each material in the manifest
    mock_responses = {
        "MP-123": {"C11": 100.0, "C12": 50.0, "C44": 28.0, "crystal_system": "fcc"},
        "MP-456": {"C11": 168.0, "C12": 121.0, "C44": 75.0, "crystal_system": "fcc"},
        "MP-789": {"C11": 246.0, "C12": 147.0, "C44": 124.0, "crystal_system": "fcc"},
        "MP-101": {"C11": 124.0, "C12": 93.0, "C44": 46.0, "crystal_system": "fcc"},
        "MP-102": {"C11": 186.0, "C12": 157.0, "C44": 42.0, "crystal_system": "fcc"}
    }

    with patch('src.data.ingest.fetch_elastic_constants') as mock_fetch:
        def side_effect(material_id):
            return mock_responses.get(material_id)
        
        mock_fetch.side_effect = side_effect

        # Step 1: Ingest data
        ingest_output = os.path.join(temp_data_dir["processed"], "elastic_constants_raw.csv")
        
        df_ingested = ingest_elastic_data(
            manifest_path=temp_manifest_file,
            output_path=ingest_output,
            force=True
        )
        
        assert len(df_ingested) == 5
        assert all(col in df_ingested.columns for col in ["material_id", "C11", "C12", "C44"])
        
        # Step 2: Clean data
        clean_output = os.path.join(temp_data_dir["processed"], "elastic_anisotropy.csv")
        
        df_cleaned = clean_elastic_data(
            input_path=ingest_output,
            output_path=clean_output,
            fcc_only=True
        )
        
        assert len(df_cleaned) == 5
        assert "A1" in df_cleaned.columns
        assert not df_cleaned["A1"].isna().any()
        
        # Step 3: Compute features
        features_output = os.path.join(temp_data_dir["processed"], "elastic_anisotropy_features.csv")
        
        df_features = compute_compositional_features(
            input_path=clean_output,
            output_path=features_output
        )
        
        assert len(df_features) == 5
        assert "atomic_radius_variance" in df_features.columns
        assert "electronegativity_std" in df_features.columns
        assert "valence_electron_concentration" in df_features.columns
        
        # Verify output files exist
        assert os.path.exists(clean_output)
        assert os.path.exists(features_output)
