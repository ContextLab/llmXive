import pytest
from data_ingestion import filter_records_with_location
from datetime import datetime

def test_filter_records_with_location():
    """Test that records with missing location are excluded."""
    records = [
        {"image_path": "img1.jpg", "location_lat": 34.05, "location_lon": -118.25, "image_date": datetime.now()},
        {"image_path": "img2.jpg", "location_lat": None, "location_lon": -118.25, "image_date": datetime.now()},
        {"image_path": "img3.jpg", "location_lat": 34.05, "location_lon": None, "image_date": datetime.now()},
        {"image_path": "img4.jpg", "location_lat": 35.0, "location_lon": -120.0, "image_date": datetime.now()},
    ]
    
    filtered = filter_records_with_location(records)
    
    assert len(filtered) == 2
    assert filtered[0]["image_path"] == "img1.jpg"
    assert filtered[1]["image_path"] == "img4.jpg"
    
    # Ensure excluded records are not in the output
    paths = [r["image_path"] for r in filtered]
    assert "img2.jpg" not in paths
    assert "img3.jpg" not in paths