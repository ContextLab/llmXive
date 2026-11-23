"""
Tests for src/config.py
"""
import os
import pytest

from src.config import Config


class TestConfigDefaults:
    """Test that Config uses correct default values."""
    
    def test_default_dataset_id(self):
        config = Config()
        assert config.RESEARCHCLAWBENCH_DATASET_ID == "researchclawbench/v1"
    
    def test_default_margin(self):
        config = Config()
        assert config.SCIENTIFIC_CORE_MARGIN == 5
    
    def test_default_max_concurrency(self):
        config = Config()
        assert config.MAX_CONCURRENCY == 7
    
    def test_default_timeout(self):
        config = Config()
        assert config.TIMEOUT_PER_RUN == 3600
    
    def test_default_budget(self):
        config = Config()
        assert config.TOTAL_WALL_CLOCK_BUDGET == 86400


class TestConfigOverrides:
    """Test that Config accepts overrides."""
    
    def test_override_dataset_id(self):
        config = Config(dataset_id="custom/dataset")
        assert config.RESEARCHCLAWBENCH_DATASET_ID == "custom/dataset"
    
    def test_override_margin(self):
        config = Config(margin=10)
        assert config.SCIENTIFIC_CORE_MARGIN == 10
    
    def test_override_concurrency(self):
        config = Config(max_concurrency=3)
        assert config.MAX_CONCURRENCY == 3
    
    def test_override_timeout(self):
        config = Config(timeout_per_run=1800)
        assert config.TIMEOUT_PER_RUN == 1800
    
    def test_override_budget(self):
        config = Config(total_budget=43200)
        assert config.TOTAL_WALL_CLOCK_BUDGET == 43200


class TestConfigLoad:
    """Test Config.load() method with environment variables."""
    
    def teardown_method(self):
        """Clean up environment variables after each test."""
        env_vars = [
            "RESEARCHCLAWBENCH_DATASET_ID",
            "SCIENTIFIC_CORE_MARGIN",
            "MAX_CONCURRENCY",
            "TIMEOUT_PER_RUN",
            "TOTAL_WALL_CLOCK_BUDGET",
        ]
        for var in env_vars:
            os.environ.pop(var, None)
    
    def test_load_uses_defaults_when_no_env(self):
        config = Config.load()
        assert config.RESEARCHCLAWBENCH_DATASET_ID == "researchclawbench/v1"
        assert config.SCIENTIFIC_CORE_MARGIN == 5
        assert config.MAX_CONCURRENCY == 7
        assert config.TIMEOUT_PER_RUN == 3600
        assert config.TOTAL_WALL_CLOCK_BUDGET == 86400
    
    def test_load_uses_env_vars(self):
        os.environ["RESEARCHCLAWBENCH_DATASET_ID"] = "env/dataset"
        os.environ["SCIENTIFIC_CORE_MARGIN"] = "10"
        os.environ["MAX_CONCURRENCY"] = "3"
        os.environ["TIMEOUT_PER_RUN"] = "1800"
        os.environ["TOTAL_WALL_CLOCK_BUDGET"] = "43200"
        
        config = Config.load()
        assert config.RESEARCHCLAWBENCH_DATASET_ID == "env/dataset"
        assert config.SCIENTIFIC_CORE_MARGIN == 10
        assert config.MAX_CONCURRENCY == 3
        assert config.TIMEOUT_PER_RUN == 1800
        assert config.TOTAL_WALL_CLOCK_BUDGET == 43200
    
    def test_load_partial_env_vars(self):
        """Test that partial env vars use defaults for missing ones."""
        os.environ["MAX_CONCURRENCY"] = "5"
        os.environ["TOTAL_WALL_CLOCK_BUDGET"] = "7200"
        
        config = Config.load()
        # Overridden values
        assert config.MAX_CONCURRENCY == 5
        assert config.TOTAL_WALL_CLOCK_BUDGET == 7200
        # Defaults for others
        assert config.RESEARCHCLAWBENCH_DATASET_ID == "researchclawbench/v1"
        assert config.SCIENTIFIC_CORE_MARGIN == 5
        assert config.TIMEOUT_PER_RUN == 3600


class TestConfigToDict:
    """Test Config.to_dict() method."""
    
    def test_to_dict_structure(self):
        config = Config()
        d = config.to_dict()
        
        assert isinstance(d, dict)
        assert "RESEARCHCLAWBENCH_DATASET_ID" in d
        assert "SCIENTIFIC_CORE_MARGIN" in d
        assert "MAX_CONCURRENCY" in d
        assert "TIMEOUT_PER_RUN" in d
        assert "TOTAL_WALL_CLOCK_BUDGET" in d
    
    def test_to_dict_values(self):
        config = Config(max_concurrency=4)
        d = config.to_dict()
        
        assert d["MAX_CONCURRENCY"] == 4
        assert d["RESEARCHCLAWBENCH_DATASET_ID"] == "researchclawbench/v1"