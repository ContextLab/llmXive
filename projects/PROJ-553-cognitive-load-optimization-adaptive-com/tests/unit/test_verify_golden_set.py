import os
import sys
import pytest
from pathlib import Path
import pandas as pd
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from verify_golden_set import verify_golden_set

class TestVerifyGoldenSet:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory structure for testing."""
        temp_path = Path(tempfile.mkdtemp())
        data_processed = temp_path / "data" / "processed"
        data_processed.mkdir(parents=True)
        yield temp_path
        shutil.rmtree(temp_path)

    def test_missing_file_exits(self, temp_dir, capsys):
        """Test that missing file triggers exit with specific error."""
        # Temporarily change the working directory to temp_dir
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            with patch('verify_golden_set.sys.exit') as mock_exit:
                verify_golden_set()
                mock_exit.assert_called_once_with(1)
                captured = capsys.readouterr()
                assert "Validation Data Missing: Golden Set or required interaction features with concurrent self-reports not found. Cannot proceed with model training." in captured.out
        finally:
            os.chdir(original_cwd)

    def test_insufficient_rows_exits(self, temp_dir, capsys):
        """Test that file with < 50 rows triggers exit."""
        df = pd.DataFrame({
            'interaction_id': range(10),
            'expert_load_score': [1.0] * 10
        })
        df.to_csv(temp_dir / "data" / "processed" / "golden_set.csv", index=False)
        
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            with patch('verify_golden_set.sys.exit') as mock_exit:
                verify_golden_set()
                mock_exit.assert_called_once_with(1)
                captured = capsys.readouterr()
                assert "Validation Data Missing: Golden Set or required interaction features with concurrent self-reports not found. Cannot proceed with model training." in captured.out
        finally:
            os.chdir(original_cwd)

    def test_missing_columns_exits(self, temp_dir, capsys):
        """Test that file without required columns triggers exit."""
        df = pd.DataFrame({
            'interaction_id': range(60),
            'other_column': [1.0] * 60
        })
        df.to_csv(temp_dir / "data" / "processed" / "golden_set.csv", index=False)
        
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            with patch('verify_golden_set.sys.exit') as mock_exit:
                verify_golden_set()
                mock_exit.assert_called_once_with(1)
                captured = capsys.readouterr()
                assert "Validation Data Missing: Golden Set or required interaction features with concurrent self-reports not found. Cannot proceed with model training." in captured.out
        finally:
            os.chdir(original_cwd)

    def test_valid_expert_score_passes(self, temp_dir, capsys):
        """Test that valid file with expert_load_score passes."""
        df = pd.DataFrame({
            'interaction_id': range(50),
            'expert_load_score': [float(i) for i in range(50)]
        })
        df.to_csv(temp_dir / "data" / "processed" / "golden_set.csv", index=False)
        
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            with patch('verify_golden_set.sys.exit') as mock_exit:
                result = verify_golden_set()
                mock_exit.assert_not_called()
                assert result is True
                captured = capsys.readouterr()
                assert "Golden Set validated" in captured.out
        finally:
            os.chdir(original_cwd)

    def test_valid_self_reports_passes(self, temp_dir, capsys):
        """Test that valid file with self-report columns passes."""
        df = pd.DataFrame({
            'interaction_id': range(50),
            'self_report_load': [float(i) for i in range(50)],
            'self_report_confidence': [float(i) for i in range(50)]
        })
        df.to_csv(temp_dir / "data" / "processed" / "golden_set.csv", index=False)
        
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            with patch('verify_golden_set.sys.exit') as mock_exit:
                result = verify_golden_set()
                mock_exit.assert_not_called()
                assert result is True
        finally:
            os.chdir(original_cwd)
