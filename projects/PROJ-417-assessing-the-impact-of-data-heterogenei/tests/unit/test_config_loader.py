import pytest
import yaml
import os
from pathlib import Path
from unittest.mock import patch, mock_open

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config_loader import (
    load_config,
    get_simulation_params,
    get_data_source_config,
    get_base_data_path,
    get_nominal_confidence_level,
    get_min_studies_for_reliability,
    get_significance_level,
    get_replicate_count,
    get_tau2_levels,
    get_random_seed,
    validate_config
)

# Sample valid config content
SAMPLE_CONFIG = """
nominal_confidence_level: 0.95
min_studies_for_reliability: 5
significance_level: 0.05

simulation_parameters:
  replicate_counts:
    primary_sweep: 500
    sensitivity_sweep: 500
    test_replicates: 1000
  tau2_levels:
    - 0.0
    - 0.1
    - 0.5
    - 1.0
    - 2.0
  random_seed: 42

synthetic_base_params:
  mean_effect: 0.5
  se_distribution:
    type: "lognormal"
    mu: 0.0
    sigma: 1.0
  study_count: 20
  seed: 42
  source_citation: "Jackson et al. (2010)"

data_source:
  type: "synthetic"
  synthetic_file: "data/raw/cochrane_base_synthetic.csv"

output:
  simulation_results_file: "data/results/simulation_raw.json"
"""

# Sample invalid config (missing required field)
INVALID_CONFIG = """
nominal_confidence_level: 0.95
# Missing min_studies_for_reliability
significance_level: 0.05
"""

@pytest.fixture
def mock_config_file(tmp_path):
    """Create a temporary config file."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(SAMPLE_CONFIG)
    return config_path

@pytest.fixture
def mock_base_data_file(tmp_path):
    """Create a temporary base data file."""
    data_path = tmp_path / "cochrane_base_synthetic.csv"
    data_path.write_text("effect,se\n0.5,0.1\n")
    return data_path

class TestLoadConfig:
    def test_load_config_success(self, mock_config_file):
        """Test successful config loading."""
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            config = load_config()
            assert config is not None
            assert config['nominal_confidence_level'] == 0.95
            assert 'simulation_parameters' in config

    def test_load_config_file_not_found(self):
        """Test FileNotFoundError when config doesn't exist."""
        fake_path = Path("/nonexistent/path/config.yaml")
        with patch('config_loader.CONFIG_PATH', fake_path):
            with pytest.raises(FileNotFoundError):
                load_config()

    def test_load_config_invalid_yaml(self, tmp_path):
        """Test error handling for invalid YAML."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("invalid: yaml: content: [")
        with patch('config_loader.CONFIG_PATH', config_path):
            with pytest.raises(Exception):  # yaml.YAMLError
                load_config()

class TestGetSimulationParams:
    def test_get_simulation_params(self, mock_config_file):
        """Test extraction of simulation parameters."""
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            params = get_simulation_params()
            assert 'replicate_counts' in params
            assert 'tau2_levels' in params
            assert params['replicate_counts']['primary_sweep'] == 500

class TestGetDataSourceConfig:
    def test_get_data_source_config(self, mock_config_file):
        """Test extraction of data source configuration."""
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            ds_config = get_data_source_config()
            assert ds_config['type'] == 'synthetic'
            assert 'synthetic_file' in ds_config

class TestGetBaseDataPath:
    def test_get_base_data_path_synthetic(self, mock_config_file, mock_base_data_file):
        """Test base data path resolution for synthetic data."""
        # Update config to point to mock data
        config_content = SAMPLE_CONFIG.replace(
            'data/raw/cochrane_base_synthetic.csv',
            str(mock_base_data_file)
        )
        mock_config_file.write_text(config_content)
        
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            path = get_base_data_path()
            assert path == mock_base_data_file
            assert path.exists()

    def test_get_base_data_path_not_found(self, mock_config_file):
        """Test FileNotFoundError when base data doesn't exist."""
        config_content = SAMPLE_CONFIG.replace(
            'data/raw/cochrane_base_synthetic.csv',
            '/nonexistent/data.csv'
        )
        mock_config_file.write_text(config_content)
        
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            with pytest.raises(FileNotFoundError):
                get_base_data_path()

class TestGetNominalConfidenceLevel:
    def test_get_nominal_confidence_level(self, mock_config_file):
        """Test extraction of confidence level."""
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            level = get_nominal_confidence_level()
            assert level == 0.95

class TestGetMinStudiesForReliability:
    def test_get_min_studies_for_reliability(self, mock_config_file):
        """Test extraction of minimum studies threshold."""
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            threshold = get_min_studies_for_reliability()
            assert threshold == 5

class TestGetSignificanceLevel:
    def test_get_significance_level(self, mock_config_file):
        """Test extraction of significance level."""
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            level = get_significance_level()
            assert level == 0.05

class TestGetReplicateCount:
    def test_get_replicate_count_primary(self, mock_config_file):
        """Test primary sweep replicate count."""
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            count = get_replicate_count(sweep_type='primary_sweep')
            assert count == 500

    def test_get_replicate_count_sensitivity(self, mock_config_file):
        """Test sensitivity sweep replicate count."""
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            count = get_replicate_count(sweep_type='sensitivity_sweep')
            assert count == 500

    def test_get_replicate_count_default(self, mock_config_file):
        """Test default replicate count for unknown sweep type."""
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            count = get_replicate_count(sweep_type='unknown_sweep')
            assert count == 500  # Default fallback

class TestGetTau2Levels:
    def test_get_tau2_levels(self, mock_config_file):
        """Test extraction of tau2 levels."""
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            levels = get_tau2_levels()
            assert levels == [0.0, 0.1, 0.5, 1.0, 2.0]
            assert all(isinstance(l, float) for l in levels)

class TestGetRandomSeed:
    def test_get_random_seed(self, mock_config_file):
        """Test extraction of random seed."""
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            seed = get_random_seed()
            assert seed == 42

class TestValidateConfig:
    def test_validate_config_success(self, mock_config_file):
        """Test successful validation."""
        with patch('config_loader.CONFIG_PATH', mock_config_file):
            assert validate_config() is True

    def test_validate_config_missing_field(self, tmp_path):
        """Test validation failure for missing required field."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(INVALID_CONFIG)
        
        with patch('config_loader.CONFIG_PATH', config_path):
            with pytest.raises(ValueError):
                validate_config()