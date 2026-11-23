import pytest
import logging
from pathlib import Path
import tempfile
import os

# Import the function to test
# Note: We assume the function is in code/ingestion.py
# Since we cannot import code directly in this test file without sys.path manipulation,
# we will simulate the logic or assume the module is importable.
# For the purpose of this task, we will import it assuming the project structure is set up.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import parse_cognitive_status, extract_metadata_and_log_exclusions

class TestParseCognitiveStatus:
    def test_valid_control(self):
        status, code = parse_cognitive_status("Subject: P001 Status: Control")
        assert status == 'Control'
        assert code == 'OK'

    def test_valid_mci(self):
        status, code = parse_cognitive_status("Subject: P002 Status: MCI")
        assert status == 'MCI'
        assert code == 'OK'

    def test_valid_ad(self):
        status, code = parse_cognitive_status("Subject: P003 Status: AD")
        assert status == 'AD'
        assert code == 'OK'

    def test_missing_status(self):
        status, code = parse_cognitive_status("Subject: P004")
        assert status == 'Unknown'
        assert code == 'MISSING_STATUS'

    def test_invalid_status(self):
        status, code = parse_cognitive_status("Subject: P005 Status: UnknownLabel")
        assert status == 'Unknown'
        assert code == 'INVALID_STATUS'

    def test_empty_header(self):
        status, code = parse_cognitive_status("")
        assert status == 'Unknown'
        assert code == 'MISSING_STATUS'

class TestExtractMetadataAndLogExclusions:
    def test_exclusion_logging(self):
        mock_transcripts = [
            {'participant_id': 'P001', 'header': 'Subject: P001 Status: Control', 'text': 'Valid text ' * 10},
            {'participant_id': 'P002', 'header': 'Subject: P002 Status: AD', 'text': 'Short'},
            {'participant_id': 'P003', 'header': 'Subject: P003', 'text': 'Valid text ' * 10},
            {'participant_id': 'P004', 'header': 'Subject: P004 Status: Invalid', 'text': 'Valid text ' * 10},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "exclusion_log.csv"
            included = extract_metadata_and_log_exclusions(mock_transcripts, log_path)
            
            # Check exclusion log exists
            assert log_path.exists()
            
            # Check included records
            assert len(included) == 1
            assert included[0]['participant_id'] == 'P001'
            
            # Check log content
            with open(log_path, 'r') as f:
                lines = f.readlines()
            
            # Header + 3 excluded records
            assert len(lines) == 4
            
            # Verify reason codes are logged
            log_content = ''.join(lines)
            assert 'Invalid metadata' in log_content or 'MISSING_STATUS' in log_content
            assert 'Text too short' in log_content

    def test_logging_integration(self):
        """Test that the logging function actually logs warnings for excluded records."""
        mock_transcripts = [
            {'participant_id': 'P001', 'header': 'Subject: P001 Status: Control', 'text': 'Valid text ' * 10},
            {'participant_id': 'P002', 'header': 'Subject: P002 Status: AD', 'text': 'Short'},
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "exclusion_log.csv"
            
            # Capture log output
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as log_file:
                log_file_path = log_file.name
            
            # Setup logger to write to file
            logger = logging.getLogger('ingestion')
            logger.setLevel(logging.WARNING)
            handler = logging.FileHandler(log_file_path)
            logger.addHandler(handler)
            
            extract_metadata_and_log_exclusions(mock_transcripts, log_path)
            
            logger.removeHandler(handler)
            handler.close()
            
            # Read log file
            with open(log_file_path, 'r') as f:
                log_content = f.read()
            
            assert 'Excluded record' in log_content
            assert 'Text too short' in log_content
            
            # Cleanup
            os.unlink(log_file_path)
