import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import os
import tempfile
from src.services.ingest import log_memory_profile
from src.services.embeddings import log_memory_profile as embed_log_memory

class TestMemoryProfiling:
    def test_log_memory_profile_ingest(self):
        """
        Test that memory profiling logs without crashing.
        """
        # Should not raise
        log_memory_profile()

    def test_log_memory_profile_embeddings(self):
        """
        Test embedding memory profiling.
        """
        embed_log_memory()

    def test_memory_profiler_not_installed(self):
        """
        Test behavior when memory_profiler is not installed.
        """
        with patch.dict('sys.modules', {'memory_profiler': None}):
            # Should handle ImportError gracefully
            try:
                log_memory_profile()
            except Exception as e:
                pytest.fail(f"log_memory_profile raised exception: {e}")
