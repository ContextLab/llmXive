"""
Unit tests for the data models (EEGDataset, APFResult, VarianceComponent).
"""
import pytest
from datetime import datetime
from pathlib import Path
import json
import tempfile
import os

from models.eeg_dataset import EEGDataset
from models.apf_result import APFResult
from models.variance_component import VarianceComponent, VarianceAnalysisResult


class TestEEGDataset:
    def test_creation(self):
        """Test basic creation of EEGDataset."""
        dataset = EEGDataset(
            dataset_id="ds003775",
            subject_ids=["sub-01", "sub-02"],
            sampling_frequency=256.0,
            channel_count=64,
        )
        
        assert dataset.dataset_id == "ds003775"
        assert len(dataset.subject_ids) == 2
        assert dataset.sampling_frequency == 256.0
        assert dataset.channel_count == 64
        assert isinstance(dataset.created_at, datetime)

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = EEGDataset(
            dataset_id="ds003865",
            subject_ids=["sub-01"],
            sampling_frequency=512.0,
            metadata={"task": "rest"},
        )
        
        data = original.to_dict()
        restored = EEGDataset.from_dict(data)
        
        assert restored.dataset_id == original.dataset_id
        assert restored.subject_ids == original.subject_ids
        assert restored.sampling_frequency == original.sampling_frequency
        assert restored.metadata == original.metadata

    def test_save_and_load_json(self):
        """Test saving to and loading from JSON file."""
        dataset = EEGDataset(
            dataset_id="ds003392",
            subject_ids=["sub-01", "sub-02", "sub-03"],
            sampling_frequency=256.0,
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "dataset.json"
            dataset.save_json(path)
            
            assert path.exists()
            
            loaded = EEGDataset.load_json(path)
            assert loaded.dataset_id == dataset.dataset_id
            assert loaded.subject_ids == dataset.subject_ids


class TestAPFResult:
    def test_creation_valid(self):
        """Test creation of a valid APFResult."""
        result = APFResult(
            dataset_id="ds003775",
            subject_id="sub-01",
            pipeline_type="Pipeline A",
            estimation_method="psd",
            apf_value=10.5,
            apf_status="valid",
        )
        
        assert result.apf_value == 10.5
        assert result.apf_status == "valid"

    def test_creation_indeterminate(self):
        """Test creation of an indeterminate result."""
        result = APFResult(
            dataset_id="ds003775",
            subject_id="sub-02",
            pipeline_type="Pipeline B",
            estimation_method="autocorr",
            apf_status="indeterminate",
        )
        
        assert result.apf_status == "indeterminate"
        assert result.apf_value is None

    def test_creation_out_of_band(self):
        """Test creation of an out-of-band result."""
        result = APFResult(
            dataset_id="ds003775",
            subject_id="sub-03",
            pipeline_type="Pipeline A",
            estimation_method="psd",
            apf_value=7.2,
            apf_status="out_of_band",
        )
        
        assert result.apf_status == "out_of_band"
        assert result.apf_value == 7.2

    def test_to_csv_row(self):
        """Test conversion to CSV row format."""
        result = APFResult(
            dataset_id="ds003775",
            subject_id="sub-01",
            confidence_interval=(10.2, 10.8),
        )
        
        row = result.to_csv_row()
        
        assert row["ci_lower"] == 10.2
        assert row["ci_upper"] == 10.8
        assert "confidence_interval" not in row


class TestVarianceComponent:
    def test_creation(self):
        """Test creation of VarianceComponent."""
        component = VarianceComponent(
            component_name="dataset_source",
            variance_estimate=0.5,
            proportion=0.35,
            p_value=0.001,
        )
        
        assert component.component_name == "dataset_source"
        assert component.variance_estimate == 0.5
        assert component.proportion == 0.35

    def test_variance_analysis_result(self):
        """Test VarianceAnalysisResult container."""
        components = [
            VarianceComponent(component_name="dataset_source", variance_estimate=0.5),
            VarianceComponent(component_name="pipeline_type", variance_estimate=0.2),
        ]
        
        analysis = VarianceAnalysisResult(
            components=components,
            total_variance=1.0,
            residual_variance=0.3,
            model_fit_stats={"AIC": 150.5, "BIC": 160.2},
        )
        
        assert len(analysis.components) == 2
        assert analysis.total_variance == 1.0
        assert analysis.model_fit_stats["AIC"] == 150.5

    def test_round_trip_serialization(self):
        """Test serialization round-trip for VarianceAnalysisResult."""
        original = VarianceAnalysisResult(
            components=[
                VarianceComponent(
                    component_name="subject_id",
                    variance_estimate=0.8,
                    confidence_interval=(0.6, 1.0),
                )
            ],
            total_variance=1.0,
        )
        
        data = original.to_dict()
        restored = VarianceAnalysisResult.from_dict(data)
        
        assert len(restored.components) == 1
        assert restored.components[0].component_name == "subject_id"
        assert restored.components[0].confidence_interval == (0.6, 1.0)
        assert restored.total_variance == 1.0
