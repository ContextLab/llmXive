"""
Contract tests for Data Models.
Verifies that the model classes match the expected schema structure
and can be serialized/deserialized correctly.
"""
import pytest
from datetime import datetime
from pathlib import Path

from models.eeg_dataset import EEGDataset
from models.apf_result import APFResult
from models.variance_component import VarianceComponent

class TestEEGDatasetSchema:
    def test_instantiation(self):
        """Test that EEGDataset can be instantiated with required fields."""
        ds = EEGDataset(
            dataset_id="ds003775",
            root_path=Path("/fake/path")
        )
        assert ds.dataset_id == "ds003775"
        assert ds.root_path == Path("/fake/path")
        assert isinstance(ds.subjects, list)
        assert ds.sampling_frequency is None

    def test_full_instantiation(self):
        """Test instantiation with all optional fields."""
        ds = EEGDataset(
            dataset_id="ds003775",
            root_path=Path("/fake/path"),
            subjects=["sub-01", "sub-02"],
            sessions=["ses-01"],
            tasks=["rest"],
            sampling_frequency=256.0,
            power_line_frequency=50.0,
            metadata={"version": "1.0.0"}
        )
        assert len(ds.subjects) == 2
        assert ds.sampling_frequency == 256.0

class TestAPFResultSchema:
    def test_valid_result(self):
        """Test a valid APF result."""
        res = APFResult(
            subject_id="sub-01",
            session_id="ses-01",
            task="rest",
            pipeline_type="pipeline_a",
            estimation_method="psd",
            apf_value=10.5,
            status="valid"
        )
        assert res.apf_value == 10.5
        assert res.status == "valid"

    def test_indeterminate_result(self):
        """Test an indeterminate result."""
        res = APFResult(
            subject_id="sub-02",
            session_id=None,
            task="rest",
            pipeline_type="pipeline_b",
            estimation_method="autocorr",
            apf_value=None,
            status="indeterminate"
        )
        assert res.apf_value is None
        assert res.status == "indeterminate"

    def test_to_dict_serialization(self):
        """Test that to_dict produces expected keys."""
        res = APFResult(
            subject_id="sub-01",
            session_id=None,
            task="rest",
            pipeline_type="pipeline_a",
            estimation_method="psd",
            apf_value=10.0
        )
        d = res.to_dict()
        expected_keys = [
            "subject_id", "session_id", "task", "pipeline_type",
            "estimation_method", "apf_value", "status", "timestamp"
        ]
        for key in expected_keys:
            assert key in d

class TestVarianceComponentSchema:
    def test_basic_component(self):
        """Test basic variance component creation."""
        vc = VarianceComponent(
            factor_name="dataset_source",
            variance_estimate=0.45,
            proportion_of_total=0.45
        )
        assert vc.factor_name == "dataset_source"
        assert vc.variance_estimate == 0.45

    def test_with_ci(self):
        """Test component with confidence intervals."""
        vc = VarianceComponent(
            factor_name="pipeline_type",
            variance_estimate=0.10,
            proportion_of_total=0.10,
            confidence_interval=(0.05, 0.15)
        )
        assert vc.confidence_interval == (0.05, 0.15)

    def test_to_dict_serialization(self):
        """Test serialization of variance component."""
        vc = VarianceComponent(
            factor_name="residual",
            variance_estimate=0.45,
            proportion_of_total=0.45
        )
        d = vc.to_dict()
        assert "factor_name" in d
        assert "variance_estimate" in d
        assert "proportion_of_total" in d