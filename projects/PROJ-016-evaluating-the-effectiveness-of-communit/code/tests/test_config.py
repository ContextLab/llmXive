"""
Unit tests for the configuration loader (T006).
"""
import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config, YEAR_RANGE, API_ENDPOINTS, PROJECT_ROOT

class TestConfig:
    """Tests for code/config.py"""

    def test_year_range_defined(self):
        """Verify YEAR_RANGE is set to (2000, 2020) as per T006 requirements."""
        assert YEAR_RANGE == (2000, 2020), f"Expected (2000, 2020), got {YEAR_RANGE}"
        assert len(YEAR_RANGE) == 2
        assert YEAR_RANGE[0] < YEAR_RANGE[1]

    def test_get_config_structure(self):
        """Verify get_config returns the expected dictionary structure."""
        config = get_config()
        
        assert "year_range" in config
        assert "paths" in config
        assert "api" in config
        assert "analysis" in config
        
        assert config["year_range"] == YEAR_RANGE

    def test_api_endpoints_exist(self):
        """Verify required API endpoints are defined."""
        assert "fao_fra" in API_ENDPOINTS
        assert "world_bank" in API_ENDPOINTS
        
        # Check FAO structure
        fao = API_ENDPOINTS["fao_fra"]
        assert "base_url" in fao
        assert "indicator_forest_area_change" in fao
        assert "timeout" in fao
        
        # Check World Bank structure
        wb = API_ENDPOINTS["world_bank"]
        assert "base_url" in wb
        assert "indicators" in wb
        assert "gdp_per_capita" in wb["indicators"]
        assert "population_density" in wb["indicators"]

    def test_paths_exist_and_valid(self):
        """Verify paths in config are valid Path objects or strings."""
        config = get_config()
        paths = config["paths"]
        
        assert "root" in paths
        assert "raw" in paths
        assert "processed" in paths
        
        # Verify they resolve correctly
        root = Path(paths["root"])
        assert root.exists(), f"Project root {root} does not exist"

    def test_api_retry_config(self):
        """Verify retry configurations are present for API stability."""
        assert API_ENDPOINTS["fao_fra"]["retry_max"] >= 3
        assert API_ENDPOINTS["world_bank"]["retry_max"] >= 3
        assert API_ENDPOINTS["fao_fra"]["timeout"] > 0
        assert API_ENDPOINTS["world_bank"]["timeout"] > 0