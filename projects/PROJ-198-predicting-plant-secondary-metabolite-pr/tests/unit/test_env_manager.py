"""
Unit tests for environment configuration management.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from config.env_manager import EnvManager, get_env_manager


class TestEnvManager:
    """Tests for EnvManager class."""

    def test_load_from_system_env(self):
        """Test loading environment variables from system."""
        os.environ['TEST_VAR'] = 'test_value'
        env = EnvManager()
        assert env.get('TEST_VAR') == 'test_value'
        del os.environ['TEST_VAR']

    def test_load_from_env_file(self):
        """Test loading environment variables from .env file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("TEST_KEY=test_value\n")
            f.write("ANOTHER_KEY=123\n")
            f.write("# This is a comment\n")
            f.write("QUOTED_KEY=\"quoted value\"\n")
            env_file = f.name

        try:
            env = EnvManager(env_file)
            assert env.get('TEST_KEY') == 'test_value'
            assert env.get('ANOTHER_KEY') == '123'
            assert env.get('QUOTED_KEY') == 'quoted value'
        finally:
            os.unlink(env_file)

    def test_ci_mode_detection(self):
        """Test CI_MODE flag detection."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("CI_MODE=true\n")
            env_file = f.name

        try:
            env = EnvManager(env_file)
            assert env.is_ci_mode is True
        finally:
            os.unlink(env_file)

        # Test default (False)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("OTHER_KEY=value\n")
            env_file = f.name

        try:
            env = EnvManager(env_file)
            assert env.is_ci_mode is False
        finally:
            os.unlink(env_file)

    def test_get_bool(self):
        """Test boolean conversion."""
        env = EnvManager()
        os.environ['BOOL_TRUE'] = 'true'
        os.environ['BOOL_FALSE'] = 'false'
        os.environ['BOOL_ONE'] = '1'
        os.environ['BOOL_ZERO'] = '0'

        assert env.get_bool('BOOL_TRUE') is True
        assert env.get_bool('BOOL_FALSE') is False
        assert env.get_bool('BOOL_ONE') is True
        assert env.get_bool('BOOL_ZERO') is False
        assert env.get_bool('NONEXISTENT', default=True) is True

        del os.environ['BOOL_TRUE']
        del os.environ['BOOL_FALSE']
        del os.environ['BOOL_ONE']
        del os.environ['BOOL_ZERO']

    def test_get_int(self):
        """Test integer conversion."""
        env = EnvManager()
        os.environ['INT_VAL'] = '42'

        assert env.get_int('INT_VAL') == 42
        assert env.get_int('NONEXISTENT', default=100) == 100
        assert env.get_int('INVALID', default=50) == 50

        del os.environ['INT_VAL']

    def test_data_paths(self):
        """Test data path properties."""
        env = EnvManager()
        assert isinstance(env.data_root, Path)
        assert isinstance(env.raw_data_path, Path)
        assert isinstance(env.processed_data_path, Path)
        assert env.raw_data_path == env.data_root / 'raw'
        assert env.processed_data_path == env.data_root / 'processed'

    def test_mock_data_paths_in_ci_mode(self):
        """Test mock data paths when in CI mode."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("CI_MODE=true\n")
            env_file = f.name

        try:
            env = EnvManager(env_file)
            assert env.is_ci_mode is True
            assert isinstance(env.mock_genomes_path, Path)
            assert isinstance(env.mock_metabolites_path, Path)
            assert isinstance(env.mock_anti_smash_path, Path)
        finally:
            os.unlink(env_file)

    def test_validate_required_keys_ci_mode(self):
        """Test validation passes in CI mode even without API keys."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("CI_MODE=true\n")
            env_file = f.name

        try:
            env = EnvManager(env_file)
            assert env.validate_required_keys() is True
        finally:
            os.unlink(env_file)

    def test_validate_required_keys_research_mode_missing_keys(self):
        """Test validation fails in research mode without API keys."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("CI_MODE=false\n")
            env_file = f.name

        try:
            env = EnvManager(env_file)
            assert env.validate_required_keys() is False
        finally:
            os.unlink(env_file)

    def test_validate_required_keys_research_mode_with_keys(self):
        """Test validation passes in research mode with API keys."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("CI_MODE=false\n")
            f.write("NCBI_API_KEY=test_key_123\n")
            env_file = f.name

        try:
            env = EnvManager(env_file)
            assert env.validate_required_keys() is True
        finally:
            os.unlink(env_file)

    def test_api_key_properties(self):
        """Test API key property access."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("NCBI_API_KEY=ncbi_key_123\n")
            f.write("METABOLIGHTS_API_KEY=metabo_key_456\n")
            env_file = f.name

        try:
            env = EnvManager(env_file)
            assert env.ncbi_api_key == 'ncbi_key_123'
            assert env.metabolights_api_key == 'metabo_key_456'
        finally:
            os.unlink(env_file)

    def test_custom_data_root(self):
        """Test custom DATA_ROOT configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("DATA_ROOT=/custom/data/path\n")
            env_file = f.name

        try:
            env = EnvManager(env_file)
            assert env.data_root == Path('/custom/data/path')
            assert env.raw_data_path == Path('/custom/data/path/raw')
        finally:
            os.unlink(env_file)

    def test_global_instance_singleton(self):
        """Test that get_env_manager returns singleton instance."""
        # Clear the global instance
        import config.env_manager as em_module
        em_module._env_manager = None

        env1 = get_env_manager()
        env2 = get_env_manager()

        assert env1 is env2

    def test_env_file_with_spaces_and_quotes(self):
        """Test parsing .env file with spaces and various quote styles."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("  SPACED_KEY = spaced_value  \n")
            f.write("SINGLE_QUOTED='single quoted'\n")
            f.write("DOUBLE_QUOTED=\"double quoted\"\n")
            f.write("MIXED='mixed \"quotes\"'\n")
            env_file = f.name

        try:
            env = EnvManager(env_file)
            assert env.get('SPACED_KEY') == 'spaced_value'
            assert env.get('SINGLE_QUOTED') == 'single quoted'
            assert env.get('DOUBLE_QUOTED') == 'double quoted'
            assert env.get('MIXED') == 'mixed "quotes"'
        finally:
            os.unlink(env_file)