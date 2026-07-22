import pytest
import pandas as pd
import json
import os
from pathlib import Path
import sys
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.preprocessing.scarcity_checker import (
    load_processed_data,
    check_scarcity,
    generate_warning_report,
    save_check_log,
    run_scarcity_check,
    THRESHOLD
)

class TestScarcityChecker:
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_processed_dir = project_root / "data" / "processed"
        self.original_data_dir = project_root / "data"
        
        # Create a fake processed directory in temp
        self.fake_processed_dir = Path(self.temp_dir) / "data" / "processed"
        self.fake_processed_dir.mkdir(parents=True)
        
        # Backup original if exists (though we won't write to it in tests)
        yield
        
        # Cleanup
        shutil.rmtree(self.temp_dir)

    def test_check_scarcity_empty_dataframe(self):
        """Test that empty dataframe returns False and triggers critical logic."""
        df = pd.DataFrame()
        result = check_scarcity(df)
        assert result is False

    def test_check_scarcity_below_threshold(self):
        """Test that N < 50 returns True (warning needed)."""
        df = pd.DataFrame({'col': range(10)})
        result = check_scarcity(df)
        assert result is True

    def test_check_scarcity_at_threshold(self):
        """Test that N = 50 returns False (no warning)."""
        df = pd.DataFrame({'col': range(50)})
        result = check_scarcity(df)
        assert result is False

    def test_check_scarcity_above_threshold(self):
        """Test that N > 50 returns False (no warning)."""
        df = pd.DataFrame({'col': range(100)})
        result = check_scarcity(df)
        assert result is False

    def test_generate_warning_report_structure(self):
        """Test that the warning report has the correct structure."""
        n = 10
        report = generate_warning_report(n, THRESHOLD)
        
        assert "n" in report
        assert report["n"] == n
        assert "threshold" in report
        assert report["threshold"] == THRESHOLD
        assert "warning" in report
        assert "status" in report
        assert report["status"] == "SCARCITY_WARNING"

    def test_save_check_log(self):
        """Test that the flag file is written correctly."""
        temp_flag_file = Path(self.temp_dir) / ".test_flag"
        report = {"n": 10, "threshold": 50, "status": "TEST"}
        
        # Temporarily override FLAG_FILE for this test
        import src.preprocessing.scarcity_checker as sc
        original_flag = sc.FLAG_FILE
        sc.FLAG_FILE = temp_flag_file
        
        try:
            save_check_log(report)
            assert temp_flag_file.exists()
            with open(temp_flag_file, 'r') as f:
                loaded = json.load(f)
            assert loaded == report
        finally:
            sc.FLAG_FILE = original_flag

    def test_load_processed_data_missing_file(self, caplog):
        """Test loading from a non-existent file."""
        # Ensure the file doesn't exist
        if INPUT_FILE.exists():
            INPUT_FILE.rename(INPUT_FILE.with_suffix('.bak'))
        
        try:
            result = load_processed_data()
            assert result is None
        finally:
            # Restore if we backed it up
            if INPUT_FILE.with_suffix('.bak').exists():
                INPUT_FILE.with_suffix('.bak').rename(INPUT_FILE)

    def test_load_processed_data_valid_file(self):
        """Test loading from a valid CSV file."""
        test_file = self.fake_processed_dir / "alloys_raw.csv"
        test_df = pd.DataFrame({'composition': ['Co2MnGa'], 'coercivity': [100]})
        test_df.to_csv(test_file, index=False)
        
        # Temporarily override INPUT_FILE
        import src.preprocessing.scarcity_checker as sc
        original_file = sc.INPUT_FILE
        sc.INPUT_FILE = test_file
        
        try:
            result = load_processed_data()
            assert result is not None
            assert len(result) == 1
            assert result.iloc[0]['composition'] == 'Co2MnGa'
        finally:
            sc.INPUT_FILE = original_file