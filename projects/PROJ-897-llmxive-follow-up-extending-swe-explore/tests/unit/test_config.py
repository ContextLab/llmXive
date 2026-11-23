"""
Unit tests for code/config.py
"""
import os
import sys
import argparse
from pathlib import Path
import pytest

# Add code to path if running from tests/
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import (
    HARD_INSTANCE_PERCENTILE,
    COVERAGE_COLUMN_NAME,
    SWEEP_SEED,
    DEFAULT_TURN_LIMIT,
    TIE_THRESHOLD,
    MAX_RUNTIME_HOURS,
    SWEEP_STABILITY_THRESHOLD,
    resolve_deferred_config,
    get_path,
    get_config_summary,
    ensure_directories,
    PROJECT_ROOT
)

class TestConfigConstants:
    """Test that hardcoded constants match specification."""

    def test_hard_instance_percentile(self):
        assert HARD_INSTANCE_PERCENTILE == 0.20

    def test_coverage_column_name(self):
        assert COVERAGE_COLUMN_NAME == 'initial_coverage'

    def test_sweep_seed(self):
        assert SWEEP_SEED == 42

    def test_default_turn_limit(self):
        assert DEFAULT_TURN_LIMIT == 3

    def test_tie_threshold(self):
        assert TIE_THRESHOLD == 0.50

    def test_max_runtime_hours(self):
        assert MAX_RUNTIME_HOURS == 6.0

    def test_sweep_stability_threshold(self):
        assert SWEEP_STABILITY_THRESHOLD == 0.05

class TestConfigResolution:
    """Test CLI and env var resolution logic."""

    def test_resolve_no_args_uses_defaults(self):
        args = argparse.Namespace(
            sweep_sample_size=None,
            model_precision=None,
            max_runtime_hours=None,
            turn_limit=None,
            mode="full"
        )
        overrides = resolve_deferred_config(args)
        # Should be empty if no args and no env vars set
        assert len(overrides) == 0

    def test_resolve_cli_args(self):
        args = argparse.Namespace(
            sweep_sample_size=100,
            model_precision="4-bit",
            max_runtime_hours=12.0,
            turn_limit=5,
            mode="full"
        )
        overrides = resolve_deferred_config(args)
        assert overrides['SWEEP_SAMPLE_SIZE'] == 100
        assert overrides['MODEL_PRECISION'] == "4-bit"
        assert overrides['MAX_RUNTIME_HOURS'] == 12.0
        assert overrides['DEFAULT_TURN_LIMIT'] == 5

    def test_resolve_env_vars(self):
        # Set env vars
        old_env = os.environ.get('SWEEP_SAMPLE_SIZE')
        os.environ['SWEEP_SAMPLE_SIZE'] = "50"
        
        try:
            args = argparse.Namespace(
                sweep_sample_size=None,
                model_precision=None,
                max_runtime_hours=None,
                turn_limit=None,
                mode="full"
            )
            overrides = resolve_deferred_config(args)
            assert overrides['SWEEP_SAMPLE_SIZE'] == 50
        finally:
            # Restore env
            if old_env is None:
                os.environ.pop('SWEEP_SAMPLE_SIZE', None)
            else:
                os.environ['SWEEP_SAMPLE_SIZE'] = old_env

class TestPathResolution:
    """Test path generation."""

    def test_get_path_creates_dir(self, tmp_path):
        # Temporarily override PROJECT_ROOT for testing
        # Note: In real execution, this creates dirs under the actual project root.
        # Here we just test that the function logic works.
        # We can't easily mock the global PROJECT_ROOT without reloading the module.
        # Instead, we assert that get_path returns a Path object.
        p = get_path(Path("test_dir"))
        assert isinstance(p, Path)
        assert p.exists()
        assert p.is_dir()

class TestConfigSummary:
    """Test config summary generation."""

    def test_get_config_summary_returns_dict(self):
        summary = get_config_summary()
        assert isinstance(summary, dict)
        assert 'hard_instance_percentile' in summary
        assert 'paths' in summary
        assert summary['hard_instance_percentile'] == 0.20