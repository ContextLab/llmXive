import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from generate_preprocessing_stats import load_subject_logs, calculate_stats, main

class TestGeneratePreprocessingStats:
    def test_load_subject_logs_empty_dir(self, tmp_path):
        """Test loading logs from an empty directory."""
        logs = load_subject_logs(tmp_path)
        assert logs == []

    def test_load_subject_logs_with_valid_json(self, tmp_path):
        """Test loading logs from a directory with valid JSON log files."""
        log_file = tmp_path / 'subject_001_preprocess.json'
        log_data = {
            'subject_id': '001',
            'status': 'success',
            'runtime_seconds': 120.5,
            'peak_ram_gb': 2.1
        }
        with open(log_file, 'w') as f:
            json.dump(log_data, f)
        
        logs = load_subject_logs(tmp_path)
        assert len(logs) == 1
        assert logs[0]['subject_id'] == '001'
        assert logs[0]['status'] == 'success'

    def test_load_subject_logs_with_invalid_json(self, tmp_path):
        """Test loading logs ignores invalid JSON files."""
        log_file = tmp_path / 'subject_001_preprocess.json'
        with open(log_file, 'w') as f:
            f.write('{ invalid json }')
        
        logs = load_subject_logs(tmp_path)
        # Should return empty or skip invalid
        assert len(logs) == 0

    def test_calculate_stats_success(self):
        """Test calculating stats with successful subjects."""
        logs = [
            {'subject_id': '001', 'status': 'success'},
            {'subject_id': '002', 'status': 'success'},
            {'subject_id': '003', 'status': 'failed'}
        ]
        stats = calculate_stats(logs)
        assert stats['total_subjects'] == 3
        assert stats['successful_subjects'] == 2
        assert stats['success_rate_percentage'] == pytest.approx(66.67, rel=0.1)

    def test_calculate_stats_no_logs(self):
        """Test calculating stats with no logs."""
        logs = []
        stats = calculate_stats(logs, total_expected=10)
        assert stats['total_subjects'] == 10 # Fallback to expected
        assert stats['successful_subjects'] == 0
        assert stats['success_rate_percentage'] == 0.0

    def test_main_generates_artifact(self, tmp_path):
        """Test that main() generates the preprocessing_stats.json artifact."""
        # Setup a temporary processed directory with a mock log
        processed_dir = tmp_path / 'data' / 'processed'
        processed_dir.mkdir(parents=True)
        
        log_file = processed_dir / 'subject_001_preprocess.json'
        log_data = {'subject_id': '001', 'status': 'success'}
        with open(log_file, 'w') as f:
            json.dump(log_data, f)
        
        # Temporarily change the working directory or mock the path
        # Since main() uses hardcoded 'data/processed', we need to run it in a context
        # where 'data/processed' points to our tmp_path.
        # We will monkeypatch the Path or run the function in a subprocess.
        # For simplicity in unit test, we will mock the internal calls or change cwd.
        
        original_cwd = os.getcwd()
        try:
            # Create a temp dir structure that mimics the project root
            project_root = tmp_path / 'project'
            project_root.mkdir()
            os.chdir(project_root)
            
            # Create data/processed
            (project_root / 'data' / 'processed').mkdir(parents=True)
            
            # Copy the mock log
            src_log = processed_dir / 'subject_001_preprocess.json'
            dst_log = project_root / 'data' / 'processed' / 'subject_001_preprocess.json'
            shutil.copy(src_log, dst_log)
            
            # Run main
            main()
            
            # Verify artifact exists
            stats_path = project_root / 'data' / 'processed' / 'preprocessing_stats.json'
            assert stats_path.exists()
            
            with open(stats_path, 'r') as f:
                stats = json.load(f)
            
            assert 'total_subjects' in stats
            assert 'successful_subjects' in stats
            assert 'success_rate_percentage' in stats
            assert stats['successful_subjects'] == 1
            assert stats['total_subjects'] == 1
            assert stats['success_rate_percentage'] == 100.0
        finally:
            os.chdir(original_cwd)