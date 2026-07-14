"""
Unit tests for the base data model classes.

Tests verify that AlloyRecord, EnvironmentRecord, and CorrosionMeasurement
correctly enforce data types, ranges, and required fields.
"""
import pytest
from datetime import datetime
from code.data.models import AlloyRecord, EnvironmentRecord, CorrosionMeasurement

class TestAlloyRecord:
    """Tests for the AlloyRecord dataclass."""

    def test_valid_creation(self):
        """Test creating a valid AlloyRecord."""
        alloy = AlloyRecord(
            alloy_id="AL001",
            designation="304L",
            composition={"Fe": 0.70, "Cr": 0.18, "Ni": 0.10, "C": 0.02}
        )
        assert alloy.alloy_id == "AL001"
        assert alloy.designation == "304L"
        assert alloy.composition["Cr"] == 0.18

    def test_empty_alloy_id_raises(self):
        """Test that empty alloy_id raises ValueError."""
        with pytest.raises(ValueError, match="alloy_id cannot be empty"):
            AlloyRecord(
                alloy_id="",
                designation="304L",
                composition={"Fe": 0.70}
            )

    def test_empty_designation_raises(self):
        """Test that empty designation raises ValueError."""
        with pytest.raises(ValueError, match="designation cannot be empty"):
            AlloyRecord(
                alloy_id="AL001",
                designation="",
                composition={"Fe": 0.70}
            )

    def test_empty_composition_raises(self):
        """Test that empty composition raises ValueError."""
        with pytest.raises(ValueError, match="composition dictionary cannot be empty"):
            AlloyRecord(
                alloy_id="AL001",
                designation="304L",
                composition={}
            )

    def test_invalid_fraction_type_raises(self):
        """Test that non-numeric fraction raises TypeError."""
        with pytest.raises(TypeError):
            AlloyRecord(
                alloy_id="AL001",
                designation="304L",
                composition={"Fe": "0.70"}
            )

    def test_fraction_out_of_range_raises(self):
        """Test that fraction outside [0, 1] raises ValueError."""
        with pytest.raises(ValueError):
            AlloyRecord(
                alloy_id="AL001",
                designation="304L",
                composition={"Fe": 1.5}
            )

    def test_to_dict(self):
        """Test serialization to dictionary."""
        alloy = AlloyRecord(
            alloy_id="AL001",
            designation="304L",
            composition={"Fe": 0.70, "Cr": 0.18},
            source="NIST"
        )
        d = alloy.to_dict()
        assert d["alloy_id"] == "AL001"
        assert d["source"] == "NIST"
        assert "created_at" in d

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "alloy_id": "AL001",
            "designation": "304L",
            "composition": {"Fe": 0.70, "Cr": 0.18},
            "source": "NIST"
        }
        alloy = AlloyRecord.from_dict(data)
        assert alloy.alloy_id == "AL001"
        assert alloy.source == "NIST"


class TestEnvironmentRecord:
    """Tests for the EnvironmentRecord dataclass."""

    def test_valid_creation(self):
        """Test creating a valid EnvironmentRecord."""
        env = EnvironmentRecord(
            env_id="ENV001",
            ph=7.0,
            temperature_c=25.0,
            solution_composition={"Cl-": 0.5},
            aeration="aerated"
        )
        assert env.env_id == "ENV001"
        assert env.ph == 7.0
        assert env.solution_composition["Cl-"] == 0.5

    def test_empty_env_id_raises(self):
        """Test that empty env_id raises ValueError."""
        with pytest.raises(ValueError, match="env_id cannot be empty"):
            EnvironmentRecord(env_id="")

    def test_invalid_ph_type_raises(self):
        """Test that non-numeric pH raises TypeError."""
        with pytest.raises(TypeError):
            EnvironmentRecord(
                env_id="ENV001",
                ph="7.0"
            )

    def test_invalid_temperature_type_raises(self):
        """Test that non-numeric temperature raises TypeError."""
        with pytest.raises(TypeError):
            EnvironmentRecord(
                env_id="ENV001",
                temperature_c="25"
            )

    def test_temperature_below_absolute_zero_raises(self):
        """Test that temperature below -273.15 raises ValueError."""
        with pytest.raises(ValueError):
            EnvironmentRecord(
                env_id="ENV001",
                temperature_c=-300.0
            )

    def test_to_dict(self):
        """Test serialization to dictionary."""
        env = EnvironmentRecord(
            env_id="ENV001",
            ph=7.0,
            source="NIST"
        )
        d = env.to_dict()
        assert d["env_id"] == "ENV001"
        assert d["ph"] == 7.0

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "env_id": "ENV001",
            "ph": 7.0,
            "temperature_c": 25.0
        }
        env = EnvironmentRecord.from_dict(data)
        assert env.env_id == "ENV001"
        assert env.temperature_c == 25.0


class TestCorrosionMeasurement:
    """Tests for the CorrosionMeasurement dataclass."""

    def test_valid_creation(self):
        """Test creating a valid CorrosionMeasurement."""
        meas = CorrosionMeasurement(
            measurement_id="MEAS001",
            alloy_id="AL001",
            env_id="ENV001",
            corrosion_potential_mv=-250.0,
            method="potentiodynamic"
        )
        assert meas.measurement_id == "MEAS001"
        assert meas.corrosion_potential_mv == -250.0

    def test_empty_measurement_id_raises(self):
        """Test that empty measurement_id raises ValueError."""
        with pytest.raises(ValueError, match="measurement_id cannot be empty"):
            CorrosionMeasurement(
                measurement_id="",
                alloy_id="AL001",
                env_id="ENV001"
            )

    def test_empty_alloy_id_ref_raises(self):
        """Test that empty alloy_id reference raises ValueError."""
        with pytest.raises(ValueError, match="alloy_id reference cannot be empty"):
            CorrosionMeasurement(
                measurement_id="MEAS001",
                alloy_id="",
                env_id="ENV001"
            )

    def test_empty_env_id_ref_raises(self):
        """Test that empty env_id reference raises ValueError."""
        with pytest.raises(ValueError, match="env_id reference cannot be empty"):
            CorrosionMeasurement(
                measurement_id="MEAS001",
                alloy_id="AL001",
                env_id=""
            )

    def test_invalid_potential_type_raises(self):
        """Test that non-numeric potential raises TypeError."""
        with pytest.raises(TypeError):
            CorrosionMeasurement(
                measurement_id="MEAS001",
                alloy_id="AL001",
                env_id="ENV001",
                corrosion_potential_mv="250"
            )

    def test_negative_corrosion_rate_mpy_raises(self):
        """Test that negative corrosion rate mpy raises ValueError."""
        with pytest.raises(ValueError):
            CorrosionMeasurement(
                measurement_id="MEAS001",
                alloy_id="AL001",
                env_id="ENV001",
                corrosion_rate_mpy=-1.0
            )

    def test_negative_corrosion_rate_mm_y_raises(self):
        """Test that negative corrosion rate mm/y raises ValueError."""
        with pytest.raises(ValueError):
            CorrosionMeasurement(
                measurement_id="MEAS001",
                alloy_id="AL001",
                env_id="ENV001",
                corrosion_rate_mm_y=-0.1
            )

    def test_to_json_and_from_json(self):
        """Test JSON serialization and deserialization."""
        meas = CorrosionMeasurement(
            measurement_id="MEAS001",
            alloy_id="AL001",
            env_id="ENV001",
            corrosion_potential_mv=-250.0
        )
        json_str = meas.to_json()
        restored = CorrosionMeasurement.from_json(json_str)
        assert restored.measurement_id == "MEAS001"
        assert restored.corrosion_potential_mv == -250.0