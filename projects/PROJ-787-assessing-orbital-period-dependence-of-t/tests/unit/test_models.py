"""
Unit tests for data models.

Tests validation, serialization, and deserialization of PlanetRecord and GapResult.
"""
import pytest
from code.models import PlanetRecord, GapResult


class TestPlanetRecord:
    """Tests for the PlanetRecord dataclass."""

    def test_valid_creation(self):
        """Test creating a valid planet record."""
        record = PlanetRecord(
            kic_id=12345,
            period=10.5,
            period_uncertainty=0.01,
            radius=2.5,
            radius_uncertainty=0.1,
            stellar_teff=5500,
            stellar_teff_uncertainty=50
        )
        assert record.kic_id == 12345
        assert record.period == 10.5
        assert record.radius == 2.5
        assert record.stellar_teff == 5500

    def test_invalid_period(self):
        """Test that negative period raises error."""
        with pytest.raises(ValueError):
            PlanetRecord(
                kic_id=12345,
                period=-10.0,
                radius=2.5,
                stellar_teff=5500
            )

    def test_invalid_radius(self):
        """Test that negative radius raises error."""
        with pytest.raises(ValueError):
            PlanetRecord(
                kic_id=12345,
                period=10.0,
                radius=-2.5,
                stellar_teff=5500
            )

    def test_to_dict(self):
        """Test serialization to dictionary."""
        record = PlanetRecord(
            kic_id=12345,
            period=10.5,
            radius=2.5,
            stellar_teff=5500
        )
        data = record.to_dict()
        assert data["kic_id"] == 12345
        assert data["period"] == 10.5
        assert "download_timestamp" in data

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "kic_id": 12345,
            "period": 10.5,
            "radius": 2.5,
            "stellar_teff": 5500,
            "period_uncertainty": 0.01,
            "radius_uncertainty": 0.1,
            "stellar_teff_uncertainty": 50
        }
        record = PlanetRecord.from_dict(data)
        assert record.kic_id == 12345
        assert record.period == 10.5

    def test_from_dict_missing_required(self):
        """Test that missing required fields raise error."""
        data = {
            "kic_id": 12345,
            "radius": 2.5,
            # Missing period and stellar_teff
        }
        with pytest.raises(ValueError):
            PlanetRecord.from_dict(data)


class TestGapResult:
    """Tests for the GapResult dataclass."""

    def test_valid_creation(self):
        """Test creating a valid gap result."""
        result = GapResult(
            bin_id="bin_01",
            period_min=1.0,
            period_max=2.0,
            bin_center_log=0.3,
            weighted_mean_period=1.5,
            planet_count=50,
            gap_location=1.8,
            gap_location_uncertainty=0.05,
            component_1_mean=1.5,
            component_1_std=0.2,
            component_1_weight=0.4,
            component_2_mean=2.5,
            component_2_std=0.3,
            component_2_weight=0.6,
            bic_score=100.0,
            aic_score=105.0,
            bimodal_confidence=0.95,
            status="resolved"
        )
        assert result.bin_id == "bin_01"
        assert result.status == "resolved"
        assert result.gap_location == 1.8

    def test_unimodal_status(self):
        """Test creating a result with unimodal status."""
        result = GapResult(
            bin_id="bin_02",
            period_min=2.0,
            period_max=3.0,
            bin_center_log=0.5,
            weighted_mean_period=2.5,
            planet_count=30,
            gap_location=0.0,
            gap_location_uncertainty=0.0,
            component_1_mean=2.0,
            component_1_std=0.5,
            component_1_weight=1.0,
            component_2_mean=0.0,
            component_2_std=0.0,
            component_2_weight=0.0,
            bic_score=200.0,
            aic_score=205.0,
            bimodal_confidence=0.1,
            status="unimodal"
        )
        assert result.status == "unimodal"

    def test_invalid_status(self):
        """Test that invalid status raises error."""
        with pytest.raises(ValueError):
            GapResult(
                bin_id="bin_03",
                period_min=1.0,
                period_max=2.0,
                bin_center_log=0.3,
                weighted_mean_period=1.5,
                planet_count=50,
                gap_location=1.8,
                gap_location_uncertainty=0.05,
                component_1_mean=1.5,
                component_1_std=0.2,
                component_1_weight=0.4,
                component_2_mean=2.5,
                component_2_std=0.3,
                component_2_weight=0.6,
                bic_score=100.0,
                aic_score=105.0,
                bimodal_confidence=0.95,
                status="invalid_status"
            )

    def test_to_json(self):
        """Test JSON serialization."""
        result = GapResult(
            bin_id="bin_01",
            period_min=1.0,
            period_max=2.0,
            bin_center_log=0.3,
            weighted_mean_period=1.5,
            planet_count=50,
            gap_location=1.8,
            gap_location_uncertainty=0.05,
            component_1_mean=1.5,
            component_1_std=0.2,
            component_1_weight=0.4,
            component_2_mean=2.5,
            component_2_std=0.3,
            component_2_weight=0.6,
            bic_score=100.0,
            aic_score=105.0,
            bimodal_confidence=0.95,
            status="resolved"
        )
        json_str = result.to_json()
        assert "bin_01" in json_str
        assert "gap_location" in json_str

    def test_from_json(self):
        """Test JSON deserialization."""
        json_str = '''
        {
            "bin_id": "bin_01",
            "period_min": 1.0,
            "period_max": 2.0,
            "bin_center_log": 0.3,
            "weighted_mean_period": 1.5,
            "planet_count": 50,
            "gap_location": 1.8,
            "gap_location_uncertainty": 0.05,
            "component_1_mean": 1.5,
            "component_1_std": 0.2,
            "component_1_weight": 0.4,
            "component_2_mean": 2.5,
            "component_2_std": 0.3,
            "component_2_weight": 0.6,
            "bic_score": 100.0,
            "aic_score": 105.0,
            "bimodal_confidence": 0.95,
            "status": "resolved",
            "bootstrap_iterations": 1000
        }
        '''
        result = GapResult.from_json(json_str)
        assert result.bin_id == "bin_01"
        assert result.bootstrap_iterations == 1000