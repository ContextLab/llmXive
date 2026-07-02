"""
Unit tests for the configuration loader (T005).
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import Config, _get_env_str, _get_env_path, _get_env_bool, PROJECT_ROOT

class TestConfigBasics:
    def test_default_paths_exist(self):
        """Test that default paths are set correctly."""
        cfg = Config()
        assert cfg.project_root is not None
        assert cfg.data_dir.exists()
        assert cfg.data_raw.exists()
        assert cfg.data_processed.exists()
        assert cfg.contracts_dir.exists()

    def test_directories_created(self):
        """Test that __init__ creates necessary directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override environment to point to temp dir
            old_root = os.environ.get("AVIAN_SONG_PROJECT_ROOT")
            os.environ["AVIAN_SONG_PROJECT_ROOT"] = tmpdir
            
            try:
                cfg = Config()
                assert Path(tmpdir).exists()
                assert (Path(tmpdir) / "data").exists()
                assert (Path(tmpdir) / "data" / "raw").exists()
                assert (Path(tmpdir) / "data" / "processed").exists()
            finally:
                if old_root is None:
                    os.environ.pop("AVIAN_SONG_PROJECT_ROOT", None)
                else:
                    os.environ["AVIAN_SONG_PROJECT_ROOT"] = old_root

class TestEnvironmentOverrides:
    def test_env_data_dir_override(self):
        """Test that AVIAN_SONG_DATA_DIR overrides default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_val = os.environ.get("AVIAN_SONG_DATA_DIR")
            os.environ["AVIAN_SONG_DATA_DIR"] = tmpdir
            
            try:
                cfg = Config()
                assert cfg.data_dir == Path(tmpdir)
            finally:
                if old_val is None:
                    os.environ.pop("AVIAN_SONG_DATA_DIR", None)
                else:
                    os.environ["AVIAN_SONG_DATA_DIR"] = old_val

    def test_env_bool_override(self):
        """Test boolean environment variable parsing."""
        old_val = os.environ.get("AVIAN_SONG_LOG_TO_FILE")
        
        try:
            os.environ["AVIAN_SONG_LOG_TO_FILE"] = "false"
            cfg = Config()
            assert cfg.log_to_file is False
            
            os.environ["AVIAN_SONG_LOG_TO_FILE"] = "1"
            cfg2 = Config()
            assert cfg2.log_to_file is True
            
            os.environ["AVIAN_SONG_LOG_TO_FILE"] = "yes"
            cfg3 = Config()
            assert cfg3.log_to_file is True
        finally:
            if old_val is None:
                os.environ.pop("AVIAN_SONG_LOG_TO_FILE", None)
            else:
                os.environ["AVIAN_SONG_LOG_TO_FILE"] = old_val

    def test_env_float_override(self):
        """Test float environment variable parsing."""
        old_val = os.environ.get("AVIAN_SONG_SPATIAL_JOIN_RADIUS_KM")
        
        try:
            os.environ["AVIAN_SONG_SPATIAL_JOIN_RADIUS_KM"] = "25.5"
            cfg = Config()
            assert cfg.spatial_join_radius_km == 25.5
        finally:
            if old_val is None:
                os.environ.pop("AVIAN_SONG_SPATIAL_JOIN_RADIUS_KM", None)
            else:
                os.environ["AVIAN_SONG_SPATIAL_JOIN_RADIUS_KM"] = old_val

    def test_env_list_override(self):
        """Test list environment variable parsing."""
        old_val = os.environ.get("AVIAN_SONG_P_VALUE_THRESHOLDS")
        
        try:
            os.environ["AVIAN_SONG_P_VALUE_THRESHOLDS"] = "0.001,0.01,0.05"
            cfg = Config()
            assert cfg.p_value_thresholds == [0.001, 0.01, 0.05]
        finally:
            if old_val is None:
                os.environ.pop("AVIAN_SONG_P_VALUE_THRESHOLDS", None)
            else:
                os.environ["AVIAN_SONG_P_VALUE_THRESHOLDS"] = old_val

class TestConfigIO:
    def test_save_and_load(self):
        """Test saving and loading configuration to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test_config.json"
            
            cfg = Config()
            cfg.spatial_join_radius_km = 50.0
            cfg.log_level = "DEBUG"
            cfg.save(save_path)
            
            assert save_path.exists()
            
            loaded = Config.load(save_path)
            assert loaded.spatial_join_radius_km == 50.0
            assert loaded.log_level == "DEBUG"
            assert loaded.data_dir == cfg.data_dir

    def test_to_dict(self):
        """Test exporting config to dictionary."""
        cfg = Config()
        d = cfg.to_dict()
        
        assert "data_dir" in d
        assert "spatial_join_radius_km" in d
        assert "log_level" in d
        assert isinstance(d["data_dir"], str)  # Paths converted to strings

class TestHelperFunctions:
    def test_get_env_str_default(self):
        """Test _get_env_str with missing key."""
        old = os.environ.get("AVIAN_SONG_TEST_KEY")
        try:
            os.environ.pop("AVIAN_SONG_TEST_KEY", None)
            assert _get_env_str("TEST_KEY", "default") == "default"
        finally:
            if old is None:
                os.environ.pop("AVIAN_SONG_TEST_KEY", None)
            else:
                os.environ["AVIAN_SONG_TEST_KEY"] = old

    def test_get_env_str_present(self):
        """Test _get_env_str with present key."""
        old = os.environ.get("AVIAN_SONG_TEST_KEY")
        try:
            os.environ["AVIAN_SONG_TEST_KEY"] = "value"
            assert _get_env_str("TEST_KEY") == "value"
        finally:
            if old is None:
                os.environ.pop("AVIAN_SONG_TEST_KEY", None)
            else:
                os.environ["AVIAN_SONG_TEST_KEY"] = old

    def test_get_env_path_relative(self):
        """Test _get_env_path with relative path."""
        old = os.environ.get("AVIAN_SONG_TEST_PATH")
        try:
            os.environ["AVIAN_SONG_TEST_PATH"] = "data/raw"
            result = _get_env_path("TEST_PATH")
            assert result.is_absolute()
            assert result.name == "raw"
        finally:
            if old is None:
                os.environ.pop("AVIAN_SONG_TEST_PATH", None)
            else:
                os.environ["AVIAN_SONG_TEST_PATH"] = old

    def test_get_env_bool_variants(self):
        """Test various boolean string representations."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ]
        
        for val, expected in test_cases:
            old = os.environ.get("AVIAN_SONG_TEST_BOOL")
            try:
                os.environ["AVIAN_SONG_TEST_BOOL"] = val
                assert _get_env_bool("TEST_BOOL") == expected
            finally:
                if old is None:
                    os.environ.pop("AVIAN_SONG_TEST_BOOL", None)
                else:
                    os.environ["AVIAN_SONG_TEST_BOOL"] = old
