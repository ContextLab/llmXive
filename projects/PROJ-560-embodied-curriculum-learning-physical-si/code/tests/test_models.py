import pytest
from typing import Dict, Any
from src.models import DatasetRecord, AnalysisResult, SensitivitySweep

class TestDatasetRecordValidation:
    """Tests for DatasetRecord validation."""
    
    def test_valid_record(self) -> None:
        """Test creating a valid DatasetRecord."""
        record = DatasetRecord(
            pre_test_score=50.0,
            post_test_score=75.0,
            instruction_type="embodied",
            covariates={"age": 10}
        )
        assert record.pre_test_score == 50.0
        assert record.post_test_score == 75.0
        assert record.instruction_type == "embodied"
        assert record.covariates == {"age": 10}
    
    def test_missing_covariates(self) -> None:
        """Test creating a record without covariates."""
        record = DatasetRecord(
            pre_test_score=50.0,
            post_test_score=75.0,
            instruction_type="static"
        )
        assert record.covariates == {}
    
    def test_gain_score_calculation(self) -> None:
        """Test gain score assignment."""
        record = DatasetRecord(
            pre_test_score=50.0,
            post_test_score=75.0,
            instruction_type="embodied",
            gain_score=25.0
        )
        assert record.gain_score == 25.0

class TestAnalysisResultValidation:
    """Tests for AnalysisResult validation."""
    
    def test_valid_result(self) -> None:
        """Test creating a valid AnalysisResult."""
        result = AnalysisResult(
            test_name="t_test",
            statistic=2.5,
            p_value=0.01,
            effect_size=0.8,
            confidence_interval=(0.5, 1.1),
            inference_framing="associational"
        )
        assert result.test_name == "t_test"
        assert result.statistic == 2.5
        assert result.p_value == 0.01
        assert result.effect_size == 0.8
        assert result.confidence_interval == (0.5, 1.1)
        assert result.inference_framing == "associational"

class TestSensitivitySweepValidation:
    """Tests for SensitivitySweep validation."""
    
    def test_valid_sweep(self) -> None:
        """Test creating a valid SensitivitySweep."""
        sweep = SensitivitySweep(
            threshold=0.05,
            n_participants=100,
            effect_size_cohen_d=0.6,
            robustness_flag=True
        )
        assert sweep.threshold == 0.05
        assert sweep.n_participants == 100
        assert sweep.effect_size_cohen_d == 0.6
        assert sweep.robustness_flag is True