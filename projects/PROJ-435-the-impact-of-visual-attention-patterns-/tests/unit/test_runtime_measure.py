import os
import sys
import pytest
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.runtime_measure import measure_runtime

class TestMeasureRuntime:
    @patch('utils.runtime_measure.time.time')
    def test_measure_runtime(self, mock_time):
        # Mock time to return fixed values
        mock_time.side_effect = [100.0, 105.0]
        
        start_time = 100.0
        runtime = measure_runtime(start_time)
        
        assert runtime == 5.0

    @patch('utils.runtime_measure.time.time')
    def test_measure_runtime_negative(self, mock_time):
        # Should not happen in reality, but test robustness
        mock_time.side_effect = [100.0, 99.0]
        
        start_time = 100.0
        runtime = measure_runtime(start_time)
        
        assert runtime == -1.0
