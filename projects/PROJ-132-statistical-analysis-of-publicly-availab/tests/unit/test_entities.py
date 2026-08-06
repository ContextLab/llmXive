"""
Unit tests for the base data entities.

These tests verify the correctness of MigrationRecord, PhenologyMetric,
and ClimateVariable classes, including validation, serialization, and
deserialization.
"""
import pytest
from datetime import datetime
from src.models.entities import (
    MigrationRecord,
    PhenologyMetric,
    ClimateVariable,
    MigrationStatus
)


class TestMigrationRecord:
    """Tests for the MigrationRecord class."""

    def test_create_valid_record(self):
        """Test creating a valid MigrationRecord."""
        record = MigrationRecord(
            species="Turdus migratorius",
            checklist_id="12345",
            date=datetime(2023, 4, 15),
            latitude=40.7128,
            longitude=-74.0060,
            count=5,
            grid_cell="0.5x0.5_40.5_-74.0",
            week_number=15,
            year=2023
        )
        assert record.species == "Turdus migratorius"
        assert record.count == 5
        assert record.week_number == 15

    def test_create_record_with_minimal_fields(self):
        """Test creating a record with only required fields."""
        record = MigrationRecord(
            species="Turdus migratorius",
            checklist_id="12345",
            date=datetime(2023, 4, 15),
            latitude=40.7128,
            longitude=-74.0060,
            count=1
        )
        assert record.effort_distance_km is None
        assert record.is_complete is True
        assert record.status == MigrationStatus.UNKNOWN

    def test_invalid_latitude(self):
        """Test that invalid latitude raises ValueError."""
        with pytest.raises(ValueError, match="latitude must be between -90 and 90"):
            MigrationRecord(
                species="Turdus migratorius",
                checklist_id="12345",
                date=datetime(2023, 4, 15),
                latitude=91.0,
                longitude=-74.0060,
                count=5
            )

    def test_invalid_longitude(self):
        """Test that invalid longitude raises ValueError."""
        with pytest.raises(ValueError, match="longitude must be between -180 and 180"):
            MigrationRecord(
                species="Turdus migratorius",
                checklist_id="12345",
                date=datetime(2023, 4, 15),
                latitude=40.7128,
                longitude=181.0,
                count=5
            )

    def test_invalid_count(self):
        """Test that negative count raises ValueError."""
        with pytest.raises(ValueError, match="count cannot be negative"):
            MigrationRecord(
                species="Turdus migratorius",
                checklist_id="12345",
                date=datetime(2023, 4, 15),
                latitude=40.7128,
                longitude=-74.0060,
                count=-1
            )

    def test_empty_species(self):
        """Test that empty species raises ValueError."""
        with pytest.raises(ValueError, match="species cannot be empty"):
            MigrationRecord(
                species="",
                checklist_id="12345",
                date=datetime(2023, 4, 15),
                latitude=40.7128,
                longitude=-74.0060,
                count=5
            )

    def test_serialization_roundtrip(self):
        """Test that serialization and deserialization preserve data."""
        original = MigrationRecord(
            species="Turdus migratorius",
            checklist_id="12345",
            date=datetime(2023, 4, 15),
            latitude=40.7128,
            longitude=-74.0060,
            count=5,
            effort_distance_km=2.5,
            effort_duration_minutes=30,
            is_complete=True,
            grid_cell="0.5x0.5_40.5_-74.0",
            week_number=15,
            year=2023,
            status=MigrationStatus.MIGRATING,
            metadata={"observer": "John Doe"}
        )
        serialized = original.to_dict()
        deserialized = MigrationRecord.from_dict(serialized)

        assert deserialized.species == original.species
        assert deserialized.checklist_id == original.checklist_id
        assert deserialized.latitude == original.latitude
        assert deserialized.longitude == original.longitude
        assert deserialized.count == original.count
        assert deserialized.effort_distance_km == original.effort_distance_km
        assert deserialized.status == original.status
        assert deserialized.metadata == original.metadata


class TestPhenologyMetric:
    """Tests for the PhenologyMetric class."""

    def test_create_valid_metric(self):
        """Test creating a valid PhenologyMetric."""
        metric = PhenologyMetric(
            species="Turdus migratorius",
            year=2023,
            grid_cell="0.5x0.5_40.5_-74.0",
            metric_type="first_arrival",
            value=105.0,
            confidence_lower=100.0,
            confidence_upper=110.0,
            sample_size=50,
            data_quality="sufficient"
        )
        assert metric.species == "Turdus migratorius"
        assert metric.value == 105.0
        assert metric.data_quality == "sufficient"

    def test_metric_with_none_confidence(self):
        """Test creating a metric with None confidence bounds."""
        metric = PhenologyMetric(
            species="Turdus migratorius",
            year=2023,
            grid_cell="0.5x0.5_40.5_-74.0",
            metric_type="first_arrival",
            value=105.0
        )
        assert metric.confidence_lower is None
        assert metric.confidence_upper is None

    def test_invalid_confidence_bounds(self):
        """Test that invalid confidence bounds raise ValueError."""
        with pytest.raises(ValueError, match="confidence_lower must be <= confidence_upper"):
            PhenologyMetric(
                species="Turdus migratorius",
                year=2023,
                grid_cell="0.5x0.5_40.5_-74.0",
                metric_type="first_arrival",
                value=105.0,
                confidence_lower=110.0,
                confidence_upper=100.0
            )

    def test_serialization_roundtrip(self):
        """Test that serialization and deserialization preserve data."""
        original = PhenologyMetric(
            species="Turdus migratorius",
            year=2023,
            grid_cell="0.5x0.5_40.5_-74.0",
            metric_type="first_arrival",
            value=105.0,
            confidence_lower=100.0,
            confidence_upper=110.0,
            sample_size=50,
            data_quality="sufficient",
            metadata={"method": "percentile"}
        )
        serialized = original.to_dict()
        deserialized = PhenologyMetric.from_dict(serialized)

        assert deserialized.species == original.species
        assert deserialized.value == original.value
        assert deserialized.confidence_lower == original.confidence_lower
        assert deserialized.metadata == original.metadata


class TestClimateVariable:
    """Tests for the ClimateVariable class."""

    def test_create_valid_variable(self):
        """Test creating a valid ClimateVariable."""
        var = ClimateVariable(
            grid_cell="0.5x0.5_40.5_-74.0",
            year=2023,
            week_number=15,
            variable_type="temperature",
            value=15.5,
            unit="C",
            source="NOAA",
            is_imputed=False
        )
        assert var.grid_cell == "0.5x0.5_40.5_-74.0"
        assert var.value == 15.5
        assert var.is_imputed is False

    def test_invalid_week_number(self):
        """Test that invalid week_number raises ValueError."""
        with pytest.raises(ValueError, match="week_number must be between 1 and 52"):
            ClimateVariable(
                grid_cell="0.5x0.5_40.5_-74.0",
                year=2023,
                week_number=53,
                variable_type="temperature",
                value=15.5,
                unit="C"
            )

    def test_week_number_zero(self):
        """Test that week_number of 0 raises ValueError."""
        with pytest.raises(ValueError, match="week_number must be between 1 and 52"):
            ClimateVariable(
                grid_cell="0.5x0.5_40.5_-74.0",
                year=2023,
                week_number=0,
                variable_type="temperature",
                value=15.5,
                unit="C"
            )

    def test_serialization_roundtrip(self):
        """Test that serialization and deserialization preserve data."""
        original = ClimateVariable(
            grid_cell="0.5x0.5_40.5_-74.0",
            year=2023,
            week_number=15,
            variable_type="temperature",
            value=15.5,
            unit="C",
            source="NOAA",
            is_imputed=True,
            metadata={"interpolation_method": "griddata"}
        )
        serialized = original.to_dict()
        deserialized = ClimateVariable.from_dict(serialized)

        assert deserialized.grid_cell == original.grid_cell
        assert deserialized.value == original.value
        assert deserialized.is_imputed == original.is_imputed
        assert deserialized.metadata == original.metadata