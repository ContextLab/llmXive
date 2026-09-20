import pytest
from typing import Dict, Any
from src.models import DatasetRecord, AnalysisResult, SensitivitySweep


class TestDatasetRecordValidation:
    """Tests for DatasetRecord dataclass."""
    
    def test_create_record(self):
        """Test creating a valid record."""
        record = DatasetRecord(
            pre_test_score=50.0,
            post_test_score=60.0,
            instruction_type="embodied",
            covariates={"age": 10}
        )
        assert record.pre_test_score == 50.0
        assert record.post_test_score == 60.0
        assert record.instruction_type == "embodied"
        assert record.covariates == {"age": 10}
        
    def test_to_dict(self):
        """Test converting record to dict."""
        record = DatasetRecord(
            pre_test_score=50.0,
            post_test_score=60.0,
            instruction_type="static"
        )
        d = record.to_dict()
        assert d["pre_test_score"] == 50.0
        assert d["instruction_type"] == "static"
        
    def test_from_dict(self):
        """Test creating record from dict."""
        data = {
            "pre_test_score": 50.0,
            "post_test_score": 60.0,
            "instruction_type": "embodied",
            "covariates": {}
        }
        record = DatasetRecord.from_dict(data)
        assert record.pre_test_score == 50.0
        assert record.instruction_type == "embodied"


class TestAnalysisResultValidation:
    """Tests for AnalysisResult dataclass."""
    
    def test_create_result(self):
        """Test creating a valid result."""
        result = AnalysisResult(
            t_statistic=2.5,
            p_value=0.01,
            effect_size=0.8,
            confidence_interval=[0.2, 1.4],
            method="t-test"
        )
        assert result.t_statistic == 2.5
        assert result.associational_framing is True
        
    def test_to_dict(self):
        """Test converting result to dict."""
        result = AnalysisResult(
            t_statistic=2.5,
            p_value=0.01,
            effect_size=0.8,
            confidence_interval=[0.2, 1.4],
            method="t-test"
        )
        d = result.to_dict()
        assert d["method"] == "t-test"
        assert d["associational_framing"] is True


class TestSensitivitySweepValidation:
    """Tests for SensitivitySweep dataclass."""
    
    def test_create_sweep(self):
        """Test creating a valid sweep entry."""
        sweep = SensitivitySweep(
            threshold=0.05,
            effect_size=0.8,
            significant=True
        )
        assert sweep.threshold == 0.05
        assert sweep.significant is True
        
    def test_to_dict(self):
        """Test converting sweep to dict."""
        sweep = SensitivitySweep(
            threshold=0.01,
            effect_size=0.5,
            significant=False
        )
        d = sweep.to_dict()
        assert d["threshold"] == 0.01
        assert d["significant"] is False
