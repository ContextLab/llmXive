import pytest
from datetime import date
from pydantic import ValidationError

from utils.schema_loader import get_timeseries_schema, get_site_schema, get_output_schema

def test_load_timeseries_schema():
    """Test that the timeseries schema loads correctly."""
    TimeseriesRecord = get_timeseries_schema()
    
    # Valid record
    valid_data = {
        "site_id": "SITE-001",
        "observation_date": date(2023, 5, 15),
        "ndvi": 0.65,
        "cloud_cover": 5.2,
        "is_deforestation_event": False,
        "recovery_stage": "late_recovery",
        "source": "landsat8",
        "quality_flag": "GOOD"
    }
    
    record = TimeseriesRecord(**valid_data)
    assert record.site_id == "SITE-001"
    assert record.ndvi == 0.65
    assert record.recovery_stage == "late_recovery"

def test_timeseries_schema_validation():
    """Test validation rules in timeseries schema."""
    TimeseriesRecord = get_timeseries_schema()
    
    # Invalid NDVI (out of range)
    with pytest.raises(ValidationError):
        TimeseriesRecord(
            site_id="SITE-001",
            observation_date=date(2023, 5, 15),
            ndvi=1.5,  # Invalid: > 1.0
            cloud_cover=5.0,
            is_deforestation_event=False,
            recovery_stage="late_recovery",
            source="landsat8",
            quality_flag="GOOD"
        )
    
    # Invalid cloud cover
    with pytest.raises(ValidationError):
        TimeseriesRecord(
            site_id="SITE-001",
            observation_date=date(2023, 5, 15),
            ndvi=0.65,
            cloud_cover=150.0,  # Invalid: > 100
            is_deforestation_event=False,
            recovery_stage="late_recovery",
            source="landsat8",
            quality_flag="GOOD"
        )
    
    # Invalid source
    with pytest.raises(ValidationError):
        TimeseriesRecord(
            site_id="SITE-001",
            observation_date=date(2023, 5, 15),
            ndvi=0.65,
            cloud_cover=5.0,
            is_deforestation_event=False,
            recovery_stage="late_recovery",
            source="landsat7",  # Invalid: not in enum
            quality_flag="GOOD"
        )

def test_timeseries_optional_fields():
    """Test that optional fields can be omitted."""
    TimeseriesRecord = get_timeseries_schema()
    
    record = TimeseriesRecord(
        site_id="SITE-001",
        observation_date=date(2023, 5, 15),
        ndvi=0.65,
        cloud_cover=5.0,
        is_deforestation_event=False,
        recovery_stage="late_recovery",
        source="landsat8",
        quality_flag="GOOD",
        # temperature_c and precipitation_mm omitted
    )
    
    assert record.temperature_c is None
    assert record.precipitation_mm is None

def test_load_site_schema():
    """Test that the site schema loads without error."""
    # Just verify it loads; detailed testing is in T006a
    SiteRecord = get_site_schema()
    assert SiteRecord is not None

def test_load_output_schema():
    """Test that the output schema loads without error."""
    # Just verify it loads; detailed testing is in T006c
    OutputRecord = get_output_schema()
    assert OutputRecord is not None