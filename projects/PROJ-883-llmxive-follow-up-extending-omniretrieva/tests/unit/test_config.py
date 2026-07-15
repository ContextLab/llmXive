"""
Unit tests for code/config.py
"""

import pytest
import os
from pathlib import Path

# Import the config module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from config import (
    EXIT_CODE_THROTTLING_FAILURE,
    EXIT_CODE_SUCCESS,
    DEFAULT_SEED,
    DATASET_URLS,
    DATASET_CONFIGS,
    SYNTHETIC_FALLBACK_CONFIG,
    get_dataset_path,
    get_dataset_config,
    check_fallback_needed,
    get_fallback_dataset,
    PROJECT_ROOT,
    DATA_DIR,
    RESULTS_DIR,
)


class TestExitCodes:
    """Test exit code constants"""
    
    def test_throttling_failure_exit_code(self):
        """Verify EXIT_CODE_THROTTLING_FAILURE is defined as 1"""
        assert EXIT_CODE_THROTTLING_FAILURE == 1
    
    def test_success_exit_code(self):
        """Verify EXIT_CODE_SUCCESS is 0"""
        assert EXIT_CODE_SUCCESS == 0
    
    def test_exit_codes_are_unique(self):
        """Ensure exit codes are distinct"""
        codes = [EXIT_CODE_SUCCESS, EXIT_CODE_THROTTLING_FAILURE]
        assert len(codes) == len(set(codes))


class TestSeeds:
    """Test seed configuration"""
    
    def test_default_seed(self):
        """Verify default seed is 42"""
        assert DEFAULT_SEED == 42
    
    def test_seed_is_integer(self):
        """Verify seed is an integer"""
        assert isinstance(DEFAULT_SEED, int)
    
    def test_seed_not_negative(self):
        """Verify seed is non-negative"""
        assert DEFAULT_SEED >= 0


class TestPaths:
    """Test path configuration"""
    
    def test_project_root_exists(self):
        """Verify PROJECT_ROOT is a Path object"""
        assert isinstance(PROJECT_ROOT, Path)
    
    def test_data_dir_exists(self):
        """Verify DATA_DIR is defined"""
        assert isinstance(DATA_DIR, Path)
    
    def test_results_dir_exists(self):
        """Verify RESULTS_DIR is defined"""
        assert isinstance(RESULTS_DIR, Path)
    
    def test_paths_are_absolute(self):
        """Verify paths are absolute"""
        assert PROJECT_ROOT.is_absolute()
        assert DATA_DIR.is_absolute()
        assert RESULTS_DIR.is_absolute()

class TestDatasetURLs:
    """Test dataset URL configuration"""
    
    def test_ms_marco_url(self):
        """Verify MS MARCO URL exists"""
        assert "ms_marco" in DATASET_URLS
        assert DATASET_URLS["ms_marco"] == "sentence-transformers/msmarco-corpus"
    
    def test_spider_url(self):
        """Verify Spider URL exists"""
        assert "spider" in DATASET_URLS
        assert DATASET_URLS["spider"] == "spider"
    
    def test_dbpedia_url(self):
        """Verify DBpedia URL exists"""
        assert "dbpedia_sample" in DATASET_URLS
        assert DATASET_URLS["dbpedia_sample"] == "dbpedia/dbpedia-entities"
    
    def test_all_urls_are_strings(self):
        """Verify all URLs are strings"""
        for url in DATASET_URLS.values():
            assert isinstance(url, str)
    
    def test_urls_not_empty(self):
        """Verify no empty URLs"""
        for url in DATASET_URLS.values():
            assert len(url) > 0

class TestDatasetConfigs:
    """Test dataset configuration"""
    
    def test_ms_marco_config(self):
        """Verify MS MARCO config has required fields"""
        config = DATASET_CONFIGS["ms_marco"]
        assert "required_fields" in config
        assert "text" in config["required_fields"]
    
    def test_spider_config(self):
        """Verify Spider config has required fields"""
        config = DATASET_CONFIGS["spider"]
        assert "required_fields" in config
        assert "query" in config["required_fields"]
    
    def test_dbpedia_config_has_fallback(self):
        """Verify DBpedia config has fallback"""
        config = DATASET_CONFIGS["dbpedia_sample"]
        assert "fallback" in config
        assert config["fallback"] == "wikidata_sample"
    
    def test_max_samples_configured(self):
        """Verify max_samples is configured for all datasets"""
        for name, config in DATASET_CONFIGS.items():
            assert "max_samples" in config
            assert isinstance(config["max_samples"], int)
            assert config["max_samples"] > 0

class TestHelperFunctions:
    """Test helper functions"""
    
    def test_get_dataset_path_valid(self):
        """Test get_dataset_path with valid name"""
        url = get_dataset_path("ms_marco")
        assert url == "sentence-transformers/msmarco-corpus"
    
    def test_get_dataset_path_invalid(self):
        """Test get_dataset_path with invalid name raises KeyError"""
        with pytest.raises(KeyError):
            get_dataset_path("invalid_dataset")
    
    def test_get_dataset_config_valid(self):
        """Test get_dataset_config with valid name"""
        config = get_dataset_config("spider")
        assert "question" in config["required_fields"]
    
    def test_get_dataset_config_invalid(self):
        """Test get_dataset_config with invalid name raises KeyError"""
        with pytest.raises(KeyError):
            get_dataset_config("invalid_dataset")
    
    def test_check_fallback_needed(self):
        """Test fallback check for DBpedia"""
        assert check_fallback_needed("dbpedia_sample") is True
    
    def test_get_fallback_dataset(self):
        """Test getting fallback dataset name"""
        fallback = get_fallback_dataset("dbpedia_sample")
        assert fallback == "wikidata_sample"
    
    def test_get_fallback_no_fallback(self):
        """Test fallback when none exists"""
        fallback = get_fallback_dataset("ms_marco")
        assert fallback is None

class TestSyntheticFallback:
    """Test synthetic fallback configuration"""
    
    def test_fallback_enabled(self):
        """Verify synthetic fallback is enabled by default"""
        assert SYNTHETIC_FALLBACK_CONFIG["enabled"] is True
    
    def test_fallback_has_seed(self):
        """Verify fallback has seed configured"""
        assert "seed" in SYNTHETIC_FALLBACK_CONFIG
        assert isinstance(SYNTHETIC_FALLBACK_CONFIG["seed"], int)
    
    def test_fallback_graph_nodes(self):
        """Verify fallback graph nodes count"""
        assert "graph_nodes" in SYNTHETIC_FALLBACK_CONFIG
        assert SYNTHETIC_FALLBACK_CONFIG["graph_nodes"] > 0
    
    def test_fallback_graph_edges(self):
        """Verify fallback graph edges count"""
        assert "graph_edges" in SYNTHETIC_FALLBACK_CONFIG
        assert SYNTHETIC_FALLBACK_CONFIG["graph_edges"] > 0

class TestEnvironmentVariables:
    """Test environment variable handling"""
    
    def test_seed_from_env(self):
        """Test seed can be overridden via environment variable"""
        # Save original
        original = os.environ.get("LLMXIVE_SEED")
        
        try:
            # Set test value
            os.environ["LLMXIVE_SEED"] = "12345"
            # Re-import to pick up new value (in real scenario, this would be done at startup)
            # For this test, we just verify the variable is read
            import importlib
            import config
            importlib.reload(config)
            assert config.RANDOM_SEED == 12345
        finally:
            # Restore original
            if original is None:
                os.environ.pop("LLMXIVE_SEED", None)
            else:
                os.environ["LLMXIVE_SEED"] = original
            importlib.reload(config)
            assert config.RANDOM_SEED == 42 if original is None else int(original)
