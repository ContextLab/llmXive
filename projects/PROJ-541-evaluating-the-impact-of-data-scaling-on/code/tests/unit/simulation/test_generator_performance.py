import pytest
import time
import numpy as np
from pathlib import Path
import sys
from simulation.config import SimulationConfig, get_default_config

class TestGeneratorPerformance:
    def test_generation_speed(self):
        """Test generation speed."""
        config = get_default_config()
        start = time.time()
        # Generate data
        end = time.time()
        assert end - start < 1.0 # Should be fast
