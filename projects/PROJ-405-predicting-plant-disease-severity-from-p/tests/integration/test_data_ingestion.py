"""
Integration test for the data ingestion pipeline on a small subset.
Verifies that the pipeline can run, extract features, and merge with weather (mocked).
"""
import pytest
import pandas as pd
import numpy as np
import cv2
from pathlib import Path
import sys
import shutil

from data_ingestion import get_image_paths, extract_metadata_from_path, process_image_features, run_feature_extraction_pipeline, filter_records_with_location, merge_weather_and_features

@pytest.fixture
def setup_test_data(tmp_path):
    """Create a minimal realistic dataset structure for integration testing."""
    data_dir = tmp_path / "data"
    raw_dir = data_dir / "raw" / "images"
    raw_dir.mkdir(parents=True)
    
    # Create 3 dummy images with specific names that might imply metadata
    # (In real scenario, filenames might contain dates/locations, here we rely on the function logic)
    img_paths = []
    for i in range(3):
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        p = raw_dir / f"image_{i}.jpg"
        cv2.imwrite(str(p), img)
        img_paths.append(p)
    
    return {
        "base_dir": data_dir,
        "raw_dir": raw_dir,
        "image_paths": img_paths
    }

def test_full_pipeline_flow(setup_test_data, monkeypatch):
    """
    Run the feature extraction and merging logic on a small subset.
    Since we cannot call real weather APIs in a fast unit/integration test without rate limits,
    we mock the weather linker to return dummy data.
    """
    raw_dir = setup_test_data["raw_dir"]
    
    # 1. Get paths
    paths = get_image_paths(raw_dir)
    assert len(paths) == 3
    
    # 2. Extract features (this calls OpenCV)
    # We need to mock the location extraction to return valid coords for the test to pass the filter
    def mock_extract_metadata(path):
        # Return dummy metadata with valid coords
        return {
            "image_path": str(path),
            "location_lat": 40.0,
            "location_lon": -75.0,
            "image_date": "2023-06-01"
        }
    
    monkeypatch.setattr("data_ingestion.extract_metadata_from_path", mock_extract_metadata)
    
    # Run feature extraction
    df_features = run_feature_extraction_pipeline(paths)
    
    assert not df_features.empty
    assert "lesion_area_ratio" in df_features.columns
    assert "necrosis_color_index" in df_features.columns
    assert "texture_entropy" in df_features.columns
    
    # 3. Filter (should keep all since we mocked valid metadata)
    df_filtered = filter_records_with_location(df_features)
    assert len(df_filtered) == 3
    
    # 4. Mock weather linker to return dummy data
    def mock_get_weather(record):
        return {
            "mean_temp": 25.0,
            "mean_humidity": 60.0,
            "total_precipitation": 0.0
        }
    
    monkeypatch.setattr("data_ingestion.get_weather_for_record", mock_get_weather)
    
    # 5. Merge
    df_final = merge_weather_and_features(df_filtered)
    
    assert not df_final.empty
    assert "mean_temp" in df_final.columns
    assert "mean_humidity" in df_final.columns
    assert "total_precipitation" in df_final.columns
    
    # Verify non-null values
    assert df_final["mean_temp"].notnull().all()
    assert df_final["lesion_area_ratio"].notnull().all()
