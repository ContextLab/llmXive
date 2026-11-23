import pytest
import os
import tempfile
from pathlib import Path
import pandas as pd
import yaml

from src.analysis.verification import (
    load_required_n,
    load_actual_n,
    verify_sample_size,
    save_verification_report,
    run_verification
)
from src.analysis.power import save_power_analysis


class TestLoadRequiredN:
    def test_load_required_n_success(self, tmp_path):
        """Test loading required N from a valid power analysis file."""
        state_dir = tmp_path
        required_n = 500
        
        # Create a mock power analysis file
        power_data = {
            "effect_size": 0.02,
            "power": 0.80,
            "alpha": 0.05,
            "required_sample_size": required_n,
            "method": "F-test for linear regression"
        }
        
        with open(state_dir / "power_analysis.yaml", 'w') as f:
            yaml.dump(power_data, f)
        
        result = load_required_n(state_dir)
        assert result == required_n

    def test_load_required_n_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised if power file is missing."""
        with pytest.raises(FileNotFoundError):
            load_required_n(tmp_path)

    def test_load_required_n_missing_key(self, tmp_path):
        """Test that ValueError is raised if required_sample_size is missing."""
        power_data = {
            "effect_size": 0.02,
            "power": 0.80
        }
        
        with open(tmp_path / "power_analysis.yaml", 'w') as f:
            yaml.dump(power_data, f)
        
        with pytest.raises(ValueError, match="Required sample size"):
            load_required_n(tmp_path)


class TestLoadActualN:
    def test_load_actual_n_success(self, tmp_path):
        """Test loading actual N from a valid CSV file."""
        data_path = tmp_path / "features.csv"
        df = pd.DataFrame({"message_id": range(100), "emoji_count": [1] * 100})
        df.to_csv(data_path, index=False)
        
        result = load_actual_n(data_path)
        assert result == 100

    def test_load_actual_n_empty_file(self, tmp_path):
        """Test that ValueError is raised for an empty CSV."""
        data_path = tmp_path / "features.csv"
        data_path.touch()  # Create empty file
        
        with pytest.raises(ValueError, match="empty"):
            load_actual_n(data_path)

    def test_load_actual_n_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised if data file is missing."""
        with pytest.raises(FileNotFoundError):
            load_actual_n(tmp_path / "nonexistent.csv")


class TestVerifySampleSize:
    def test_verify_pass(self):
        """Test verification when actual N meets required N."""
        result = verify_sample_size(required_n=100, actual_n=150)
        assert result["status"] == "PASS"
        assert result["is_sufficient"] is True
        assert "warning" not in result

    def test_verify_warning(self):
        """Test verification when actual N is less than required N."""
        result = verify_sample_size(required_n=200, actual_n=150)
        assert result["status"] == "WARNING"
        assert result["is_sufficient"] is False
        assert "warning" in result
        assert "Power Limitation Warning" in result["warning"]

    def test_verify_exact_match(self):
        """Test verification when actual N exactly equals required N."""
        result = verify_sample_size(required_n=100, actual_n=100)
        assert result["status"] == "PASS"
        assert result["is_sufficient"] is True


class TestSaveVerificationReport:
    def test_save_report(self, tmp_path):
        """Test saving the verification report to a file."""
        result = verify_sample_size(100, 150)
        output_path = tmp_path / "verification.yaml"
        
        save_verification_report(result, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data["verification_status"] == "PASS"
        assert data["details"]["actual_sample_size"] == 150


class TestRunVerification:
    def test_run_verification_success(self, tmp_path):
        """Test the full verification workflow."""
        # Setup state directory with power analysis
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        save_power_analysis(
            state_dir=state_dir,
            effect_size=0.02,
            power=0.80,
            alpha=0.05,
            required_sample_size=50
        )
        
        # Setup data directory with features
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        data_path = data_dir / "features.csv"
        df = pd.DataFrame({"message_id": range(60), "emoji_count": [1] * 60})
        df.to_csv(data_path, index=False)
        
        # Run verification
        output_path = state_dir / "verification.yaml"
        result = run_verification(data_path, state_dir, output_path)
        
        assert result["status"] == "PASS"
        assert result["actual_sample_size"] == 60
        assert result["required_sample_size"] == 50
        assert output_path.exists()

    def test_run_verification_warning(self, tmp_path):
        """Test verification with insufficient sample size."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        save_power_analysis(
            state_dir=state_dir,
            effect_size=0.02,
            power=0.80,
            alpha=0.05,
            required_sample_size=100
        )
        
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        data_path = data_dir / "features.csv"
        df = pd.DataFrame({"message_id": range(50), "emoji_count": [1] * 50})
        df.to_csv(data_path, index=False)
        
        output_path = state_dir / "verification.yaml"
        result = run_verification(data_path, state_dir, output_path)
        
        assert result["status"] == "WARNING"
        assert result["actual_sample_size"] == 50
        assert result["required_sample_size"] == 100
        assert "Power Limitation Warning" in result["warning"]