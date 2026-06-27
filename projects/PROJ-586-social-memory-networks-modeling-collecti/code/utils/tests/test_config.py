"""Tests for the configuration management module."""

import os
import tempfile
from pathlib import Path
import pytest

from utils.config import (
    Config,
    ConfigManager,
    get_config_manager,
    get_config,
    load_config,
    reload_config,
    create_default_config,
    ensure_config_exists,
    DEFAULT_CONFIG_YAML,
)


class TestConfigDataclass:
    """Tests for the Config dataclass."""

    def test_default_values(self):
        """Test that Config has correct default values."""
        config = Config()
        assert config.seed == 42
        assert config.device == 'cpu'
        assert config.log_level == 'INFO'
        assert config.num_agents == 2
        assert config.context_window == 512
        assert config.max_games == 1000
        assert config.alpha == 0.05
        assert config.power_threshold == 0.70
        assert config.agent_counts == [3, 5, 7]

    def test_custom_values(self):
        """Test Config with custom values."""
        config = Config(
            seed=123,
            device='cuda',
            num_agents=5,
            max_games=500,
        )
        assert config.seed == 123
        assert config.device == 'cuda'
        assert config.num_agents == 5
        assert config.max_games == 500

    def test_to_dict(self):
        """Test Config.to_dict() produces expected output."""
        config = Config(seed=42, device='cpu')
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict['seed'] == 42
        assert config_dict['device'] == 'cpu'
        assert 'num_agents' in config_dict

    def test_from_dict(self):
        """Test Config.from_dict() creates correct instance."""
        data = {
            'seed': 999,
            'device': 'cuda',
            'num_agents': 7,
            'max_games': 2000,
        }
        config = Config.from_dict(data)
        assert config.seed == 999
        assert config.device == 'cuda'
        assert config.num_agents == 7
        assert config.max_games == 2000

    def test_from_dict_defaults(self):
        """Test Config.from_dict() uses defaults for missing keys."""
        data = {'seed': 42}
        config = Config.from_dict(data)
        assert config.seed == 42
        assert config.device == 'cpu'  # default
        assert config.num_agents == 2  # default

    def test_validate_success(self):
        """Test validation passes for valid values."""
        config = Config()
        config.validate()  # Should not raise

    def test_validate_invalid_seed(self):
        """Test validation fails for negative seed."""
        with pytest.raises(ValueError, match="Seed must be non-negative"):
            Config(seed=-1)

    def test_validate_invalid_device(self):
        """Test validation fails for invalid device."""
        with pytest.raises(ValueError, match="Device must be"):
            Config(device='invalid_device')

    def test_validate_invalid_num_agents(self):
        """Test validation fails for num_agents < 1."""
        with pytest.raises(ValueError, match="num_agents must be >= 1"):
            Config(num_agents=0)

    def test_validate_invalid_alpha(self):
        """Test validation fails for invalid alpha."""
        with pytest.raises(ValueError, match="alpha must be in"):
            Config(alpha=1.5)

    def test_validate_invalid_power_threshold(self):
        """Test validation fails for invalid power_threshold."""
        with pytest.raises(ValueError, match="power_threshold must be in"):
            Config(power_threshold=0.0)


class TestConfigManager:
    """Tests for the ConfigManager singleton."""

    def test_singleton(self):
        """Test that ConfigManager is a singleton."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        assert manager1 is manager2

    def test_get_config_manager(self):
        """Test get_config_manager() returns singleton."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        assert manager1 is manager2

    def test_config_property(self):
        """Test config property returns Config instance."""
        manager = ConfigManager()
        config = manager.config
        assert isinstance(config, Config)
        assert config.seed == 42  # default

    def test_reload_clears_cache(self):
        """Test reload() clears the config cache."""
        manager = ConfigManager()
        config1 = manager.config
        manager.reload()
        config2 = manager.config
        # Should be a new instance after reload
        assert config1 is not config2 or config1 != config2

    def test_get_method(self):
        """Test get() method retrieves config values."""
        manager = ConfigManager()
        assert manager.get('seed') == 42
        assert manager.get('device') == 'cpu'
        assert manager.get('nonexistent', 'default') == 'default'

    def test_set_method(self):
        """Test set() method updates config values."""
        manager = ConfigManager()
        manager.set('seed', 123)
        assert manager.get('seed') == 123


class TestConfigLoading:
    """Tests for config loading functionality."""

    def test_load_config_from_file(self):
        """Test loading config from a YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("seed: 456\ndevice: cuda\nnum_agents: 5\n")
            f.flush()
            config_path = Path(f.name)

        try:
            config = load_config(config_path)
            assert config.seed == 456
            assert config.device == 'cuda'
            assert config.num_agents == 5
        finally:
            config_path.unlink()

    def test_load_missing_file_uses_defaults(self):
        """Test that missing config file uses defaults."""
        config = load_config(Path('/nonexistent/path/config.yaml'))
        assert config.seed == 42  # default
        assert config.device == 'cpu'  # default

    def test_create_default_config(self):
        """Test creating a default config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_config.yaml'
            created_path = create_default_config(output_path)

            assert created_path.exists()
            content = created_path.read_text()
            assert 'seed: 42' in content
            assert 'device: cpu' in content

    def test_ensure_config_exists_creates(self):
        """Test ensure_config_exists creates file if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp dir to avoid polluting project
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                # No config.yaml exists
                config_path = ensure_config_exists()
                assert config_path.exists()
            finally:
                os.chdir(old_cwd)


class TestEnvironmentOverrides:
    """Tests for environment variable overrides."""

    def test_env_override_seed(self):
        """Test that environment variable overrides seed."""
        manager = ConfigManager()
        original_seed = manager.get('seed')

        os.environ['SOCIAL_MEMORY_SEED'] = '999'
        manager.reload()

        assert manager.get('seed') == 999

        # Clean up
        del os.environ['SOCIAL_MEMORY_SEED']
        manager.reload()

    def test_env_override_device(self):
        """Test that environment variable overrides device."""
        manager = ConfigManager()
        os.environ['SOCIAL_MEMORY_DEVICE'] = 'cuda'
        manager.reload()

        assert manager.get('device') == 'cuda'

        # Clean up
        del os.environ['SOCIAL_MEMORY_DEVICE']
        manager.reload()

    def test_env_override_num_agents(self):
        """Test that environment variable overrides num_agents."""
        manager = ConfigManager()
        os.environ['SOCIAL_MEMORY_NUM_AGENTS'] = '10'
        manager.reload()

        assert manager.get('num_agents') == 10

        # Clean up
        del os.environ['SOCIAL_MEMORY_NUM_AGENTS']
        manager.reload()

    def test_env_override_alpha(self):
        """Test that environment variable overrides alpha (float)."""
        manager = ConfigManager()
        os.environ['SOCIAL_MEMORY_ALPHA'] = '0.01'
        manager.reload()

        assert manager.get('alpha') == 0.01

        # Clean up
        del os.environ['SOCIAL_MEMORY_ALPHA']
        manager.reload()


class TestConfigIntegration:
    """Integration tests for config module."""

    def test_full_config_cycle(self):
        """Test complete config lifecycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'

            # Create config file
            create_default_config(config_path)
            assert config_path.exists()

            # Load config
            config = load_config(config_path)
            assert config.seed == 42
            assert config.device == 'cpu'

            # Modify config
            config.max_games = 2000
            assert config.max_games == 2000

    def test_config_with_default_yaml_content(self):
        """Test that DEFAULT_CONFIG_YAML is valid."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(DEFAULT_CONFIG_YAML)
            f.flush()
            config_path = Path(f.name)

        try:
            config = load_config(config_path)
            assert config.seed == 42
            assert config.device == 'cpu'
            assert config.num_agents == 2
            assert config.agent_counts == [3, 5, 7]
        finally:
            config_path.unlink()