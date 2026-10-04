"""
Unit tests for Pydantic models defined in contracts/models.py.
"""
import pytest
from datetime import datetime
from contracts.models import MoralResponse, TemperatureRecord, MergedDataset

def test_moral_response_valid():
    """Test valid instantiation of MoralResponse."""
    data = {
        "participant_id": "P001",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "timestamp": "2016-01-01T12:00:00",
        "response_time": 2500.5,
        "country": "GBR",
        "dilemma_id": "D001"
    }
    model = MoralResponse(**data)
    assert model.participant_id == "P001"
    assert model.response_time == 2500.5
    assert isinstance(model.timestamp, datetime)

def test_moral_response_invalid_lat():
    """Test validation failure for invalid latitude."""
    with pytest.raises(ValueError):
        MoralResponse(
            participant_id="P001",
            latitude=100.0,  # Out of range
            longitude=-0.1278,
            timestamp="2016-01-01T12:00:00",
            response_time=2500.5,
            country="GBR",
            dilemma_id="D001"
        )

def test_temperature_record_valid():
    """Test valid instantiation of TemperatureRecord."""
    data = {
        "grid_id": "GRID_001",
        "timestamp": "2016-01-01T12:00:00",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "temperature_celsius": 15.5
    }
    model = TemperatureRecord(**data)
    assert model.grid_id == "GRID_001"
    assert model.temperature_celsius == 15.5

def test_merged_dataset_valid():
    """Test valid instantiation of MergedDataset."""
    data = {
        "participant_id": "P001",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "timestamp": "2016-01-01T12:00:00",
        "response_time": 2500.5,
        "country": "GBR",
        "dilemma_id": "D001",
        "grid_id": "GRID_001",
        "temperature_celsius": 15.5,
        "dilemma_choice": "save_many",
        "dilemma_complexity": 3.5,
        "time_of_day": "afternoon",
        "cultural_region": "Western Europe"
    }
    model = MergedDataset(**data)
    assert model.dilemma_choice == "save_many"
    assert model.dilemma_complexity == 3.5