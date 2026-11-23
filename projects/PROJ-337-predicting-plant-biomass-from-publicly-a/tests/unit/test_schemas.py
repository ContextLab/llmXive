"""
Unit tests for Pydantic schemas in code/models/schemas.py.

These tests verify that schemas correctly parse valid JSON examples
and reject invalid data as per the data-model.md specifications.
"""
import pytest
import json
from code.models.schemas import (
    SpectralBand,
    RawSpectralRecord,
    ProcessedRecord,
    BiomassLabel,
    TrainingSample,
    ModelPrediction
)


class TestSpectralBand:
    """Tests for SpectralBand schema."""
    
    def test_valid_band(self):
        """Test parsing a valid spectral band."""
        data = {
            "wavelength_nm": 550.5,
            "reflectance": 0.45,
            "band_name": "Green"
        }
        band = SpectralBand(**data)
        assert band.wavelength_nm == 550.5
        assert band.reflectance == 0.45
        assert band.band_name == "Green"
    
    def test_band_without_name(self):
        """Test band without optional name."""
        data = {
            "wavelength_nm": 650.0,
            "reflectance": 0.32
        }
        band = SpectralBand(**data)
        assert band.band_name is None
    
    def test_reflectance_below_zero(self):
        """Test that reflectance < 0 raises validation error."""
        data = {
            "wavelength_nm": 550.0,
            "reflectance": -0.1
        }
        with pytest.raises(Exception):
            SpectralBand(**data)
    
    def test_reflectance_above_one(self):
        """Test that reflectance > 1 raises validation error."""
        data = {
            "wavelength_nm": 550.0,
            "reflectance": 1.5
        }
        with pytest.raises(Exception):
            SpectralBand(**data)
    
    def test_missing_required_field(self):
        """Test that missing wavelength raises error."""
        data = {
            "reflectance": 0.5
        }
        with pytest.raises(Exception):
            SpectralBand(**data)


class TestRawSpectralRecord:
    """Tests for RawSpectralRecord schema."""
    
    def test_valid_record(self):
        """Test parsing a valid raw spectral record."""
        data = {
            "site_id": "NEON.D01.BART",
            "scene_id": "20230615_001",
            "timestamp": "2023-06-15T14:30:00Z",
            "latitude": 42.536,
            "longitude": -72.195,
            "bands": [
                {"wavelength_nm": 450.0, "reflectance": 0.15, "band_name": "Blue"},
                {"wavelength_nm": 550.0, "reflectance": 0.25, "band_name": "Green"},
                {"wavelength_nm": 650.0, "reflectance": 0.35, "band_name": "Red"}
            ],
            "cloud_flag": False
        }
        record = RawSpectralRecord(**data)
        assert record.site_id == "NEON.D01.BART"
        assert len(record.bands) == 3
        assert record.cloud_flag is False
    
    def test_cloud_flag_true(self):
        """Test record with cloud contamination."""
        data = {
            "site_id": "NEON.D01.BART",
            "scene_id": "20230615_002",
            "timestamp": "2023-06-15T14:35:00Z",
            "latitude": 42.536,
            "longitude": -72.195,
            "bands": [{"wavelength_nm": 550.0, "reflectance": 0.5}],
            "cloud_flag": True
        }
        record = RawSpectralRecord(**data)
        assert record.cloud_flag is True
    
    def test_invalid_latitude(self):
        """Test that latitude outside [-90, 90] raises error."""
        data = {
            "site_id": "NEON.D01.BART",
            "scene_id": "20230615_001",
            "timestamp": "2023-06-15T14:30:00Z",
            "latitude": 95.0,
            "longitude": -72.195,
            "bands": [{"wavelength_nm": 550.0, "reflectance": 0.3}],
            "cloud_flag": False
        }
        with pytest.raises(Exception):
            RawSpectralRecord(**data)
    
    def test_empty_bands_list(self):
        """Test that empty bands list raises error."""
        data = {
            "site_id": "NEON.D01.BART",
            "scene_id": "20230615_001",
            "timestamp": "2023-06-15T14:30:00Z",
            "latitude": 42.536,
            "longitude": -72.195,
            "bands": [],
            "cloud_flag": False
        }
        with pytest.raises(Exception):
            RawSpectralRecord(**data)


class TestProcessedRecord:
    """Tests for ProcessedRecord schema."""
    
    def test_valid_processed_record(self):
        """Test parsing a valid processed record."""
        data = {
            "record_id": "REC-001",
            "site_id": "NEON.D01.BART",
            "scene_id": "20230615_001",
            "timestamp": "2023-06-15T14:30:00Z",
            "latitude": 42.536,
            "longitude": -72.195,
            "corrected_reflectance": {
                "Blue": 0.12,
                "Green": 0.22,
                "Red": 0.31,
                "NIR": 0.45
            },
            "structural_features": {
                "NDVI": 0.65,
                "LAI": 2.3
            },
            "cloud_flag": False
        }
        record = ProcessedRecord(**data)
        assert record.record_id == "REC-001"
        assert record.structural_features["NDVI"] == 0.65
    
    def test_without_structural_features(self):
        """Test record without structural features."""
        data = {
            "record_id": "REC-002",
            "site_id": "NEON.D01.BART",
            "scene_id": "20230615_002",
            "timestamp": "2023-06-15T14:35:00Z",
            "latitude": 42.536,
            "longitude": -72.195,
            "corrected_reflectance": {"Red": 0.35},
            "cloud_flag": False
        }
        record = ProcessedRecord(**data)
        assert record.structural_features is None
    
    def test_with_exclusion_reason(self):
        """Test record with exclusion reason."""
        data = {
            "record_id": "REC-003",
            "site_id": "NEON.D01.BART",
            "scene_id": "20230615_003",
            "timestamp": "2023-06-15T14:40:00Z",
            "latitude": 42.536,
            "longitude": -72.195,
            "corrected_reflectance": {"Red": 0.40},
            "cloud_flag": True,
            "exclusion_reason": "Cloud cover > 30%"
        }
        record = ProcessedRecord(**data)
        assert record.exclusion_reason == "Cloud cover > 30%"


class TestBiomassLabel:
    """Tests for BiomassLabel schema."""
    
    def test_valid_label(self):
        """Test parsing a valid biomass label."""
        data = {
            "sample_id": "SAMP-001",
            "site_id": "NEON.D01.BART",
            "collection_date": "2023-06-15",
            "dry_mass_g": 125.5,
            "wet_mass_g": 350.2,
            "species": "Quercus rubra",
            "measurement_method": "Harvest and dry"
        }
        label = BiomassLabel(**data)
        assert label.dry_mass_g == 125.5
        assert label.species == "Quercus rubra"
    
    def test_without_wet_mass(self):
        """Test label without wet mass."""
        data = {
            "sample_id": "SAMP-002",
            "site_id": "NEON.D01.BART",
            "collection_date": "2023-06-16",
            "dry_mass_g": 89.3,
            "measurement_method": "Harvest and dry"
        }
        label = BiomassLabel(**data)
        assert label.wet_mass_g is None
    
    def test_invalid_dry_mass_zero(self):
        """Test that dry_mass_g <= 0 raises error."""
        data = {
            "sample_id": "SAMP-003",
            "site_id": "NEON.D01.BART",
            "collection_date": "2023-06-17",
            "dry_mass_g": 0.0,
            "measurement_method": "Harvest and dry"
        }
        with pytest.raises(Exception):
            BiomassLabel(**data)


class TestTrainingSample:
    """Tests for TrainingSample schema."""
    
    def test_valid_training_sample(self):
        """Test parsing a valid training sample."""
        data = {
            "sample_id": "TRAIN-001",
            "record_id": "REC-001",
            "site_id": "NEON.D01.BART",
            "features": {
                "Red": 0.31,
                "NIR": 0.45,
                "NDVI": 0.65
            },
            "target": 125.5,
            "metadata": {
                "season": "summer",
                "phenology": "leaf_on"
            }
        }
        sample = TrainingSample(**data)
        assert sample.target == 125.5
        assert sample.metadata["season"] == "summer"


class TestModelPrediction:
    """Tests for ModelPrediction schema."""
    
    def test_valid_prediction(self):
        """Test parsing a valid model prediction."""
        data = {
            "sample_id": "PRED-001",
            "predicted_biomass_g": 130.2,
            "confidence_interval": (120.5, 140.0),
            "model_version": "v1.0.0"
        }
        prediction = ModelPrediction(**data)
        assert prediction.predicted_biomass_g == 130.2
        assert prediction.confidence_interval == (120.5, 140.0)
    
    def test_without_confidence_interval(self):
        """Test prediction without confidence interval."""
        data = {
            "sample_id": "PRED-002",
            "predicted_biomass_g": 95.8,
            "model_version": "v1.0.0"
        }
        prediction = ModelPrediction(**data)
        assert prediction.confidence_interval is None
    
    def test_invalid_predicted_biomass_zero(self):
        """Test that predicted_biomass_g <= 0 raises error."""
        data = {
            "sample_id": "PRED-003",
            "predicted_biomass_g": 0.0,
            "model_version": "v1.0.0"
        }
        with pytest.raises(Exception):
            ModelPrediction(**data)


class TestJSONParsing:
    """Tests for parsing JSON strings directly."""
    
    def test_parse_raw_record_from_json(self):
        """Test parsing RawSpectralRecord from JSON string."""
        json_str = json.dumps({
            "site_id": "NEON.D01.BART",
            "scene_id": "20230615_001",
            "timestamp": "2023-06-15T14:30:00Z",
            "latitude": 42.536,
            "longitude": -72.195,
            "bands": [
                {"wavelength_nm": 550.0, "reflectance": 0.25, "band_name": "Green"}
            ],
            "cloud_flag": False
        })
        record = RawSpectralRecord.model_validate_json(json_str)
        assert record.site_id == "NEON.D01.BART"
    
    def test_parse_processed_record_from_json(self):
        """Test parsing ProcessedRecord from JSON string."""
        json_str = json.dumps({
            "record_id": "REC-001",
            "site_id": "NEON.D01.BART",
            "scene_id": "20230615_001",
            "timestamp": "2023-06-15T14:30:00Z",
            "latitude": 42.536,
            "longitude": -72.195,
            "corrected_reflectance": {"NIR": 0.45},
            "cloud_flag": False
        })
        record = ProcessedRecord.model_validate_json(json_str)
        assert record.corrected_reflectance["NIR"] == 0.45
    
    def test_parse_biomass_label_from_json(self):
        """Test parsing BiomassLabel from JSON string."""
        json_str = json.dumps({
            "sample_id": "SAMP-001",
            "site_id": "NEON.D01.BART",
            "collection_date": "2023-06-15",
            "dry_mass_g": 125.5,
            "measurement_method": "Harvest and dry"
        })
        label = BiomassLabel.model_validate_json(json_str)
        assert label.dry_mass_g == 125.5
    
    def test_parse_training_sample_from_json(self):
        """Test parsing TrainingSample from JSON string."""
        json_str = json.dumps({
            "sample_id": "TRAIN-001",
            "record_id": "REC-001",
            "site_id": "NEON.D01.BART",
            "features": {"NDVI": 0.65},
            "target": 125.5
        })
        sample = TrainingSample.model_validate_json(json_str)
        assert sample.features["NDVI"] == 0.65
    
    def test_parse_model_prediction_from_json(self):
        """Test parsing ModelPrediction from JSON string."""
        json_str = json.dumps({
            "sample_id": "PRED-001",
            "predicted_biomass_g": 130.2,
            "model_version": "v1.0.0"
        })
        prediction = ModelPrediction.model_validate_json(json_str)
        assert prediction.predicted_biomass_g == 130.2


class TestExtraFields:
    """Tests for extra='forbid' configuration."""
    
    def test_forbid_extra_field_in_band(self):
        """Test that extra fields in SpectralBand raise error."""
        data = {
            "wavelength_nm": 550.0,
            "reflectance": 0.3,
            "invalid_field": "should_fail"
        }
        with pytest.raises(Exception):
            SpectralBand(**data)
    
    def test_forbid_extra_field_in_record(self):
        """Test that extra fields in RawSpectralRecord raise error."""
        data = {
            "site_id": "NEON.D01.BART",
            "scene_id": "20230615_001",
            "timestamp": "2023-06-15T14:30:00Z",
            "latitude": 42.536,
            "longitude": -72.195,
            "bands": [{"wavelength_nm": 550.0, "reflectance": 0.3}],
            "cloud_flag": False,
            "invalid_extra": "should_fail"
        }
        with pytest.raises(Exception):
            RawSpectralRecord(**data)
    
    def test_forbid_extra_field_in_label(self):
        """Test that extra fields in BiomassLabel raise error."""
        data = {
            "sample_id": "SAMP-001",
            "site_id": "NEON.D01.BART",
            "collection_date": "2023-06-15",
            "dry_mass_g": 125.5,
            "measurement_method": "Harvest and dry",
            "unknown_field": "should_fail"
        }
        with pytest.raises(Exception):
            BiomassLabel(**data)