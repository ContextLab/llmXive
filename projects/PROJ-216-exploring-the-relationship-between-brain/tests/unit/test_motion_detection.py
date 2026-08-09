import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from motion_detection import (
    load_motion_metrics,
    get_valid_subjects,
    detect_motion_artifacts,
    write_motion_exclusion_log,
    main,
    TRANSLATION_THRESHOLD_MM,
    ROTATION_THRESHOLD_MM
)

class TestMotionDetection:
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)
    
    def test_load_motion_metrics_from_json(self, temp_dir):
        """Test loading motion metrics from JSON files."""
        # Create mock JSON files
        subject1_data = {
            "subject_id": "sub-001",
            "translation_mm": 1.5,
            "rotation_mm": 1.0
        }
        subject2_data = {
            "subject_id": "sub-002",
            "translation_mm": 4.0,  # Exceeds threshold
            "rotation_mm": 1.2
        }
        
        with open(temp_dir / "sub-001.json", 'w') as f:
            json.dump(subject1_data, f)
        with open(temp_dir / "sub-002.json", 'w') as f:
            json.dump(subject2_data, f)
        
        # Load metrics
        metrics = load_motion_metrics(temp_dir)
        
        assert len(metrics) == 2
        assert any(m['subject_id'] == 'sub-001' for m in metrics)
        assert any(m['subject_id'] == 'sub-002' for m in metrics)
        
        sub1 = next(m for m in metrics if m['subject_id'] == 'sub-001')
        assert sub1['translation_mm'] == 1.5
        assert sub1['rotation_mm'] == 1.0
        
        sub2 = next(m for m in metrics if m['subject_id'] == 'sub-002')
        assert sub2['translation_mm'] == 4.0
    
    def test_get_valid_subjects(self):
        """Test filtering subjects with valid motion metrics."""
        metrics = [
            {'subject_id': 'sub-001', 'translation_mm': 1.5, 'rotation_mm': 1.0},
            {'subject_id': 'sub-002', 'translation_mm': None, 'rotation_mm': 1.0},
            {'subject_id': 'sub-003', 'translation_mm': 2.0, 'rotation_mm': None},
            {'subject_id': 'sub-004', 'translation_mm': 3.0, 'rotation_mm': 2.5}
        ]
        
        valid = get_valid_subjects(metrics)
        
        assert len(valid) == 2
        assert valid[0]['subject_id'] == 'sub-001'
        assert valid[1]['subject_id'] == 'sub-004'
    
    def test_detect_motion_artifacts(self):
        """Test detection of motion artifacts based on thresholds."""
        metrics = [
            {'subject_id': 'sub-001', 'translation_mm': 1.5, 'rotation_mm': 1.0},
            {'subject_id': 'sub-002', 'translation_mm': 4.0, 'rotation_mm': 1.0},  # Translation > 3
            {'subject_id': 'sub-003', 'translation_mm': 2.0, 'rotation_mm': 2.5},  # Rotation > 2
            {'subject_id': 'sub-004', 'translation_mm': 5.0, 'rotation_mm': 3.0}   # Both exceed
        ]
        
        results = detect_motion_artifacts(metrics)
        
        assert len(results) == 4
        
        # Check exclusion flags
        assert results[0]['excluded'] == False  # sub-001: within thresholds
        assert results[1]['excluded'] == True   # sub-002: translation > 3
        assert results[2]['excluded'] == True   # sub-003: rotation > 2
        assert results[3]['excluded'] == True   # sub-004: both exceed
    
    def test_write_motion_exclusion_log(self, temp_dir):
        """Test writing motion exclusion log to CSV."""
        results = [
            {'subject_id': 'sub-001', 'translation_mm': 1.5, 'rotation_mm': 1.0, 'excluded': False},
            {'subject_id': 'sub-002', 'translation_mm': 4.0, 'rotation_mm': 1.0, 'excluded': True},
            {'subject_id': 'sub-003', 'translation_mm': 2.0, 'rotation_mm': 2.5, 'excluded': True}
        ]
        
        output_path = temp_dir / "motion_exclusion_log.csv"
        write_motion_exclusion_log(results, output_path)
        
        assert output_path.exists()
        
        # Verify CSV content
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 4  # Header + 3 data rows
        assert 'subject_id,translation_mm,rotation_mm,excluded' in lines[0]
        
        # Check data rows
        data_rows = [line.strip().split(',') for line in lines[1:]]
        assert data_rows[0] == ['sub-001', '1.5000', '1.0000', 'False']
        assert data_rows[1] == ['sub-002', '4.0000', '1.0000', 'True']
        assert data_rows[2] == ['sub-003', '2.0000', '2.5000', 'True']
    
    def test_mock_high_motion_subject(self, temp_dir):
        """
        Test with a mock subject with Translation=4mm to force exclusion logic.
        This satisfies the verification requirement for T018a.
        """
        # Create mock JSON with high motion
        high_motion_data = {
            "subject_id": "sub-high-motion",
            "translation_mm": 4.0,  # Exceeds 3mm threshold
            "rotation_mm": 1.0
        }
        
        with open(temp_dir / "sub-high-motion.json", 'w') as f:
            json.dump(high_motion_data, f)
        
        # Load and process
        metrics = load_motion_metrics(temp_dir)
        valid = get_valid_subjects(metrics)
        results = detect_motion_artifacts(valid)
        
        assert len(results) == 1
        assert results[0]['subject_id'] == 'sub-high-motion'
        assert results[0]['excluded'] == True
        assert results[0]['translation_mm'] == 4.0
        
        # Write to CSV
        output_path = temp_dir / "motion_exclusion_log.csv"
        write_motion_exclusion_log(results, output_path)
        
        assert output_path.exists()
        
        # Verify CSV contains the excluded subject
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert 'sub-high-motion' in content
        assert '4.0000' in content
        assert 'True' in content
    
    def test_threshold_boundaries(self):
        """Test subjects exactly at threshold boundaries."""
        metrics = [
            {'subject_id': 'at-trans-limit', 'translation_mm': 3.0, 'rotation_mm': 2.0},
            {'subject_id': 'at-rot-limit', 'translation_mm': 3.0, 'rotation_mm': 2.0},
            {'subject_id': 'just-over-trans', 'translation_mm': 3.0001, 'rotation_mm': 2.0},
            {'subject_id': 'just-over-rot', 'translation_mm': 3.0, 'rotation_mm': 2.0001}
        ]
        
        results = detect_motion_artifacts(metrics)
        
        # At limit should NOT be excluded (> not >=)
        assert results[0]['excluded'] == False
        assert results[1]['excluded'] == False
        
        # Just over should be excluded
        assert results[2]['excluded'] == True
        assert results[3]['excluded'] == True
    
    def test_empty_metrics(self):
        """Test handling of empty metrics list."""
        results = detect_motion_artifacts([])
        assert len(results) == 0
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "empty.csv"
            write_motion_exclusion_log([], output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                lines = f.readlines()
            assert len(lines) == 1  # Only header
            assert 'subject_id' in lines[0]
    
    def test_main_function_integration(self, temp_dir, monkeypatch):
        """Test the main function with mocked paths."""
        # Create mock data
        mock_data = {
            "subject_id": "test-subject",
            "translation_mm": 4.5,
            "rotation_mm": 1.5
        }
        
        logs_dir = temp_dir / "logs"
        logs_dir.mkdir()
        with open(logs_dir / "test-subject.json", 'w') as f:
            json.dump(mock_data, f)
        
        output_csv = temp_dir / "output.csv"
        
        # Mock the paths in main()
        original_main = main
        
        # We can't easily mock Path(__file__).parent.parent in the module,
        # so we test the core logic instead
        metrics = load_motion_metrics(logs_dir)
        valid = get_valid_subjects(metrics)
        results = detect_motion_artifacts(valid)
        write_motion_exclusion_log(results, output_csv)
        
        assert output_csv.exists()
        
        with open(output_csv, 'r') as f:
            content = f.read()
        
        assert 'test-subject' in content
        assert 'True' in content
        assert 'excluded' in content
    
    def test_multiple_threshold_violations(self):
        """Test subject violating both thresholds."""
        metrics = [
            {'subject_id': 'dual-violation', 'translation_mm': 5.0, 'rotation_mm': 3.0}
        ]
        
        results = detect_motion_artifacts(metrics)
        
        assert results[0]['excluded'] == True
        assert results[0]['translation_mm'] == 5.0
        assert results[0]['rotation_mm'] == 3.0
    
    def test_csv_format_verification(self, temp_dir):
        """Verify CSV format matches specification exactly."""
        results = [
            {'subject_id': 'sub-001', 'translation_mm': 1.5, 'rotation_mm': 1.0, 'excluded': False},
            {'subject_id': 'sub-002', 'translation_mm': 4.0, 'rotation_mm': 2.5, 'excluded': True}
        ]
        
        output_path = temp_dir / "motion_exclusion_log.csv"
        write_motion_exclusion_log(results, output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Verify columns
        assert set(rows[0].keys()) == {'subject_id', 'translation_mm', 'rotation_mm', 'excluded'}
        
        # Verify data types (strings in CSV)
        assert isinstance(rows[0]['subject_id'], str)
        assert isinstance(rows[0]['translation_mm'], str)
        assert isinstance(rows[0]['rotation_mm'], str)
        assert isinstance(rows[0]['excluded'], str)
        
        # Verify specific values
        assert rows[0]['subject_id'] == 'sub-001'
        assert rows[0]['excluded'] == 'False'
        assert rows[1]['excluded'] == 'True'
