"""
Unit tests for the data models and entities in code/models.py.
"""
import pytest
import pandas as pd
from code.models import (
    Jurisdiction,
    Discrepancy,
    DiscrepancyType,
    create_discrepancy_record,
    validate_output_schema,
    SCHEMA_COLUMNS
)


@pytest.fixture
def sample_jurisdiction():
    return Jurisdiction(
        name="Fulton County",
        state="GA",
        election_year=2020,
        level="county"
    )


def test_jurisdiction_creation(sample_jurisdiction):
    assert sample_jurisdiction.name == "Fulton County"
    assert sample_jurisdiction.state == "GA"
    assert sample_jurisdiction.election_year == 2020
    assert sample_jurisdiction.level == "county"

def test_jurisdiction_hash(sample_jurisdiction):
    j1 = Jurisdiction("A", "B", 2020)
    j2 = Jurisdiction("A", "B", 2020)
    j3 = Jurisdiction("A", "B", 2021)
    assert hash(j1) == hash(j2)
    assert hash(j1) != hash(j3)

def test_discrepancy_normal_case(sample_jurisdiction):
    """Test standard calculation where precinct_sum < county_reported."""
    d = create_discrepancy_record(
        precinct_sum=100.0,
        county_reported=105.0,
        jurisdiction=sample_jurisdiction
    )
    assert d.precinct_sum == 100.0
    assert d.county_reported == 105.0
    assert d.discrepancy_abs == 5.0
    assert abs(d.discrepancy_pct - (5.0/105.0)*100) < 0.0001
    assert d.missing_data is False
    assert d.discrepancy_type == DiscrepancyType.NORMAL

def test_discrepancy_directional_anomaly(sample_jurisdiction):
    """Test case where precinct_sum > county_reported (anomaly)."""
    d = create_discrepancy_record(
        precinct_sum=110.0,
        county_reported=100.0,
        jurisdiction=sample_jurisdiction
    )
    assert d.discrepancy_abs == 10.0
    assert d.discrepancy_type == DiscrepancyType.DIRECTIONAL_ANOMALY

def test_discrepancy_zero_county_reported(sample_jurisdiction):
    """Test handling of division by zero when county_reported is 0."""
    d = create_discrepancy_record(
        precinct_sum=0.0,
        county_reported=0.0,
        jurisdiction=sample_jurisdiction
    )
    assert d.discrepancy_pct == 0.0
    assert d.discrepancy_abs == 0.0

def test_discrepancy_missing_data_flag(sample_jurisdiction):
    """Test that missing_data flag sets type to MISSING_DATA."""
    d = create_discrepancy_record(
        precinct_sum=100.0,
        county_reported=105.0,
        jurisdiction=sample_jurisdiction,
        missing_data=True
    )
    assert d.missing_data is True
    assert d.discrepancy_type == DiscrepancyType.MISSING_DATA

def test_discrepancy_from_dict(sample_jurisdiction):
    data = {
        'precinct_sum': 50.0,
        'county_reported': 52.0,
        'discrepancy_abs': 2.0,
        'discrepancy_pct': 3.84,
        'missing_data': False,
        'raw_row_id': 'row-123'
    }
    d = Discrepancy.from_dict(data, sample_jurisdiction)
    assert d.precinct_sum == 50.0
    assert d.raw_row_id == 'row-123'
    assert d.discrepancy_abs == 2.0

def test_validate_output_schema_success():
    """Test validation with correct schema."""
    df = pd.DataFrame({
        'precinct_sum': [1.0],
        'county_reported': [2.0],
        'discrepancy_abs': [1.0],
        'discrepancy_pct': [50.0],
        'missing_data': [False]
    })
    assert validate_output_schema(df) is True

def test_validate_output_schema_missing_column():
    """Test validation with a missing required column."""
    df = pd.DataFrame({
        'precinct_sum': [1.0],
        'county_reported': [2.0],
        # Missing 'discrepancy_abs'
        'discrepancy_pct': [50.0],
        'missing_data': [False]
    })
    assert validate_output_schema(df) is False

def test_schema_columns_constant():
    """Ensure the schema constant matches the expected output columns."""
    expected = ['precinct_sum', 'county_reported', 'discrepancy_abs', 'discrepancy_pct', 'missing_data']
    assert SCHEMA_COLUMNS == expected
