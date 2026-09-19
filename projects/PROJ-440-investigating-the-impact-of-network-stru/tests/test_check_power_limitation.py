import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path

from code.check_power_limitation import (
    load_data,
    check_power_limitation,
    write_warning_message
)

class TestPowerLimitationCheck:
    @pytest.fixture
    def valid_networks_csv(self, tmp_path):
        """Create a valid networks CSV with 50 samples (10 per class)."""
        csv_path = tmp_path / "networks_valid.csv"
        classes = ['random', 'scale_free', 'small_world', 'lattice', 'star']
        data = []
        for cls in classes:
            for i in range(10):
                data.append({
                    'id': f"{cls}_{i}",
                    'class': cls,
                    'N': 100,
                    'clustering': 0.5,
                    'path_length': 5.0
                })
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    @pytest.fixture
    def insufficient_networks_csv(self, tmp_path):
        """Create a networks CSV with insufficient samples (5 per class)."""
        csv_path = tmp_path / "networks_insufficient.csv"
        classes = ['random', 'scale_free', 'small_world', 'lattice', 'star']
        data = []
        for cls in classes:
            for i in range(5):  # Only 5 per class
                data.append({
                    'id': f"{cls}_{i}",
                    'class': cls,
                    'N': 100,
                    'clustering': 0.5,
                    'path_length': 5.0
                })
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    def test_load_data_success(self, valid_networks_csv):
        """Test successful loading of valid CSV."""
        df = load_data(valid_networks_csv)
        assert len(df) == 50
        assert 'class' in df.columns
        assert 'clustering' in df.columns

    def test_load_data_file_not_found(self, tmp_path):
        """Test loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_data(str(tmp_path / "nonexistent.csv"))

    def test_load_data_empty_file(self, tmp_path):
        """Test loading empty file raises ValueError."""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("id,class,N,clustering,path_length\n")
        with pytest.raises(ValueError):
            load_data(str(csv_path))

    def test_check_power_limitation_valid(self, valid_networks_csv):
        """Test power check passes with valid dataset."""
        df = load_data(valid_networks_csv)
        result = check_power_limitation(df, min_samples_per_class=10, num_classes=5)

        assert result['valid'] is True
        assert result['total_samples'] == 50
        assert result['required_total'] == 50
        assert len(result['missing_classes']) == 0

    def test_check_power_limitation_insufficient_total(self, insufficient_networks_csv):
        """Test power check fails when total samples are insufficient."""
        df = load_data(insufficient_networks_csv)
        result = check_power_limitation(df, min_samples_per_class=10, num_classes=5)

        assert result['valid'] is False
        assert result['total_samples'] == 25
        assert result['required_total'] == 50
        assert len(result['missing_classes']) == 5  # All classes insufficient

    def test_check_power_limitation_partial_insufficiency(self, tmp_path):
        """Test power check fails when some classes are insufficient."""
        csv_path = tmp_path / "partial.csv"
        data = [
            {'id': 'r1', 'class': 'random', 'N': 100, 'clustering': 0.5, 'path_length': 5.0},
            {'id': 'r2', 'class': 'random', 'N': 100, 'clustering': 0.5, 'path_length': 5.0},
            # Only 2 random, 0 others
        ]
        pd.DataFrame(data).to_csv(csv_path, index=False)
        df = load_data(str(csv_path))
        result = check_power_limitation(df, min_samples_per_class=10, num_classes=5)

        assert result['valid'] is False
        assert 'Class' in result['message']

    def test_write_warning_message_creates_file(self, tmp_path, insufficient_networks_csv):
        """Test that warning file is created when check fails."""
        df = load_data(insufficient_networks_csv)
        result = check_power_limitation(df, min_samples_per_class=10, num_classes=5)
        warning_path = str(tmp_path / "power_warning.txt")

        write_warning_message(result, warning_path)

        assert Path(warning_path).exists()
        content = Path(warning_path).read_text()
        assert "Power requirement" in content
        assert "FAILED" in content

    def test_write_warning_message_no_file_on_success(self, tmp_path, valid_networks_csv):
        """Test that warning file is NOT created when check passes."""
        df = load_data(valid_networks_csv)
        result = check_power_limitation(df, min_samples_per_class=10, num_classes=5)
        warning_path = str(tmp_path / "power_warning.txt")

        write_warning_message(result, warning_path)

        # File should not exist if valid
        assert not Path(warning_path).exists()
