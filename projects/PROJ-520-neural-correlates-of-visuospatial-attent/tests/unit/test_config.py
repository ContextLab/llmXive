import pytest
import os
import json
import tempfile
from pathlib import Path

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from config import (
    get_default_config,
    get_env_config,
    deep_merge,
    load_config,
    get_config,
    set_random_seed,
    get_seed,
    get_paths,
    ensure_directories
)

class TestConfigDefaults:
    def test_default_config_keys(self):
        config = get_default_config()
        assert 'SEED' in config
        assert 'DATA_PATH' in config
        assert 'OUTPUT_PATH' in config
        assert 'BENCHMARK_ACCURACY' in config
        assert 'RAM_LIMIT_GB' in config
        assert 'CPU_LIMIT' in config

    def test_benchmark_accuracy_default_is_none(self):
        # Per T006 requirement: BENCHMARK_ACCURACY is None (deferred)
        config = get_default_config()
        assert config['BENCHMARK_ACCURACY'] is None

    def test_seed_default_is_42(self):
        config = get_default_config()
        assert config['SEED'] == 42

class TestDeepMerge:
    def test_simple_override(self):
        base = {'a': 1, 'b': 2}
        override = {'b': 3}
        result = deep_merge(base, override)
        assert result['a'] == 1
        assert result['b'] == 3

    def test_nested_merge(self):
        base = {'a': {'x': 1}}
        override = {'a': {'y': 2}}
        result = deep_merge(base, override)
        assert result['a']['x'] == 1
        assert result['a']['y'] == 2

class TestLoadConfig:
    def test_load_from_json_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'SEED': 100}, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config['SEED'] == 100
            assert config['BENCHMARK_ACCURACY'] is None  # Default preserved
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file_uses_default(self):
        config = load_config('/nonexistent/path/config.json')
        assert config['SEED'] == 42

class TestEnvConfig:
    def test_env_override_seed(self):
        original = os.environ.get('SEED')
        try:
            os.environ['SEED'] = '999'
            env_cfg = get_env_config()
            assert env_cfg['SEED'] == 999
        finally:
            if original is not None:
                os.environ['SEED'] = original
            elif 'SEED' in os.environ:
                del os.environ['SEED']

    def test_env_override_benchmark_accuracy(self):
        original = os.environ.get('BENCHMARK_ACCURACY')
        try:
            os.environ['BENCHMARK_ACCURACY'] = '75.5'
            env_cfg = get_env_config()
            assert env_cfg['BENCHMARK_ACCURACY'] == 75.5
        finally:
            if original is not None:
                os.environ['BENCHMARK_ACCURACY'] = original
            elif 'BENCHMARK_ACCURACY' in os.environ:
                del os.environ['BENCHMARK_ACCURACY']

    def test_env_override_benchmark_accuracy_none(self):
        original = os.environ.get('BENCHMARK_ACCURACY')
        try:
            os.environ['BENCHMARK_ACCURACY'] = 'none'
            env_cfg = get_env_config()
            assert env_cfg['BENCHMARK_ACCURACY'] is None
        finally:
            if original is not None:
                os.environ['BENCHMARK_ACCURACY'] = original
            elif 'BENCHMARK_ACCURACY' in os.environ:
                del os.environ['BENCHMARK_ACCURACY']

class TestPaths:
    def test_paths_exist(self):
        paths = get_paths()
        assert 'data' in paths
        assert 'output' in paths
        assert 'base' in paths
        assert isinstance(paths['data'], str)
        assert isinstance(paths['output'], str)

class TestRandomSeed:
    def test_set_random_seed_determinism(self):
        set_random_seed(123)
        val1 = np.random.random()
        set_random_seed(123)
        val2 = np.random.random()
        assert val1 == val2