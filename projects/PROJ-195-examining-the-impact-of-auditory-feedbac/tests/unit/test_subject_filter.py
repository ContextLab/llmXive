import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from subject_filter import load_qc_log, filter_valid_subjects, write_valid_subjects

class TestLoadQcLog:
    def test_load_valid_qc_log(self, tmp_path):
        """Test loading a properly formatted QC log."""
        qc_content = """
        2023-10-27 10:00:00 - subject_filter - INFO - Subject sub-01: max_displacement=1.23mm (PASS)
        2023-10-27 10:01:00 - subject_filter - INFO - Subject sub-02: max_displacement=0.85mm (PASS)
        2023-10-27 10:02:00 - subject_filter - INFO - Subject sub-03: max_displacement=2.50mm (FAIL)
        """
        qc_file = tmp_path / 'preprocessing_qc.log'
        qc_file.write_text(qc_content)
        
        result = load_qc_log(qc_file)
        
        assert 'sub-01' in result
        assert result['sub-01'] == 1.23
        assert 'sub-02' in result
        assert result['sub-02'] == 0.85
        assert 'sub-03' in result
        assert result['sub-03'] == 2.50

    def test_load_missing_qc_log(self, tmp_path):
        """Test that loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_qc_log(tmp_path / 'nonexistent.log')

    def test_load_empty_qc_log(self, tmp_path):
        """Test that an empty log raises ValueError."""
        qc_file = tmp_path / 'empty.log'
        qc_file.write_text('')
        
        with pytest.raises(ValueError, match="No valid subject motion data found"):
            load_qc_log(qc_file)

class TestFilterValidSubjects:
    def test_filter_with_threshold(self):
        """Test filtering subjects with a 2.0mm threshold."""
        qc_data = {
            'sub-01': 1.0,
            'sub-02': 1.99,
            'sub-03': 2.0,
            'sub-04': 2.01,
            'sub-05': 3.5
        }
        
        valid, excluded = filter_valid_subjects(qc_data, motion_threshold=2.0)
        
        assert valid == ['sub-01', 'sub-02', 'sub-03']
        assert len(excluded) == 2
        assert excluded[0] == ('sub-04', 2.01)
        assert excluded[1] == ('sub-05', 3.5)

    def test_filter_all_pass(self):
        """Test when all subjects pass the threshold."""
        qc_data = {'sub-01': 0.5, 'sub-02': 1.5}
        
        valid, excluded = filter_valid_subjects(qc_data, motion_threshold=2.0)
        
        assert valid == ['sub-01', 'sub-02']
        assert excluded == []

    def test_filter_all_fail(self):
        """Test when all subjects fail the threshold."""
        qc_data = {'sub-01': 2.1, 'sub-02': 5.0}
        
        valid, excluded = filter_valid_subjects(qc_data, motion_threshold=2.0)
        
        assert valid == []
        assert len(excluded) == 2

class TestWriteValidSubjects:
    def test_write_valid_subjects_file(self, tmp_path):
        """Test writing valid subjects to a file."""
        valid_subjects = ['sub-01', 'sub-02', 'sub-03']
        output_file = tmp_path / 'valid_subjects.txt'
        
        write_valid_subjects(valid_subjects, output_file)
        
        assert output_file.exists()
        content = output_file.read_text().strip().split('\n')
        assert content == valid_subjects

    def test_write_creates_directories(self, tmp_path):
        """Test that write_valid_subjects creates parent directories."""
        valid_subjects = ['sub-01']
        output_file = tmp_path / 'nested' / 'dir' / 'valid_subjects.txt'
        
        write_valid_subjects(valid_subjects, output_file)
        
        assert output_file.exists()
        assert output_file.parent.exists()
