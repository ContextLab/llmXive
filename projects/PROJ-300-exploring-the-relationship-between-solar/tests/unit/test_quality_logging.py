import pytest
import json
import logging
import tempfile
from pathlib import Path
import sys
from datetime import datetime

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / 'code'
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from main import log_quality_warnings

class TestQualityLogging:
    def test_log_quality_warnings_creates_file(self, tmp_path):
        """Test that quality warnings are written to JSON file."""
        output_path = tmp_path / 'quality_log.json'
        
        warnings = [
            {
                'type': 'gap',
                'message': 'Data gap detected in solar wind data',
                'timestamp': datetime.now().isoformat()
            },
            {
                'type': 'nan',
                'message': 'NaN values detected in THEMIS data',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        # Create a mock logger
        logger = logging.getLogger('test')
        
        log_quality_warnings(logger, warnings, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            content = json.load(f)
        
        assert len(content) == 2
        assert content[0]['type'] == 'gap'
        assert content[1]['type'] == 'nan'

    def test_log_quality_warnings_appends_to_existing(self, tmp_path):
        """Test that new warnings are appended to existing log."""
        output_path = tmp_path / 'quality_log.json'
        
        # Create initial log
        initial_warnings = [
            {
                'type': 'initial',
                'message': 'Initial warning',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        with open(output_path, 'w') as f:
            json.dump(initial_warnings, f)
        
        new_warnings = [
            {
                'type': 'new',
                'message': 'New warning',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        logger = logging.getLogger('test')
        log_quality_warnings(logger, new_warnings, output_path)
        
        with open(output_path, 'r') as f:
            content = json.load(f)
        
        assert len(content) == 2
        assert content[0]['type'] == 'initial'
        assert content[1]['type'] == 'new'

    def test_log_quality_warnings_empty_list(self, tmp_path):
        """Test that empty warning list doesn't modify existing log."""
        output_path = tmp_path / 'quality_log.json'
        
        # Create initial log
        initial_warnings = [
            {
                'type': 'initial',
                'message': 'Initial warning',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        with open(output_path, 'w') as f:
            json.dump(initial_warnings, f)
        
        logger = logging.getLogger('test')
        log_quality_warnings(logger, [], output_path)
        
        with open(output_path, 'r') as f:
            content = json.load(f)
        
        assert len(content) == 1
        assert content[0]['type'] == 'initial'