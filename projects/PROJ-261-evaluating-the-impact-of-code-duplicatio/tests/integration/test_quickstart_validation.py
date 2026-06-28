"""Integration tests for quickstart validation."""

import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestQuickstartValidation:
    """Test suite for quickstart validation."""

    def test_config_parameters_exist(self):
        """Test that all required config parameters exist."""
        from config import get_all_config

        config = get_all_config()
        required_params = [
            'clone_thresholds',
            'random_seed',
            'memory_limit_mb',
            'max_runtime_seconds',
            'min_valid_segments',
            'correlation_method',
            'significance_threshold',
            'figure_format',
            'figure_dpi',
            'checksum_algorithm',
            'dataset_name',
            'model_name',
            'quantization_bits',
            'streaming_enabled',
            'pii_scan_enabled',
        ]

        for param in required_params:
            assert param in config, f"Missing config parameter: {param}"

    def test_directory_structure_exists(self):
        """Test that required directories exist."""
        required_dirs = [
            project_root / 'data' / 'raw',
            project_root / 'data' / 'processed',
            project_root / 'data' / 'analysis',
        ]

        for dir_path in required_dirs:
            assert dir_path.exists(), f"Missing directory: {dir_path}"

    def test_checksum_manifest_can_load(self):
        """Test that checksum manifest can be loaded if it exists."""
        from checksum_manifest import load_manifest

        manifest_path = project_root / 'data' / 'checksum_manifest.json'

        if manifest_path.exists():
            manifest = load_manifest(manifest_path)
            assert 'artifact_hashes' in manifest

    def test_quickstart_validation_script_exists(self):
        """Test that the quickstart validation script exists."""
        validation_script = project_root / 'code' / 'quickstart_validation.py'
        assert validation_script.exists(), "Quickstart validation script not found"

    def test_quickstart_script_is_valid_python(self):
        """Test that the quickstart validation script is valid Python."""
        validation_script = project_root / 'code' / 'quickstart_validation.py'

        with open(validation_script, 'r', encoding='utf-8') as f:
            source = f.read()

        # Try to compile the script
        try:
            compile(source, str(validation_script), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Syntax error in quickstart_validation.py: {e}")

    def test_quickstart_documentation_exists(self):
        """Test that quickstart documentation exists."""
        quickstart_path = project_root / 'specs' / '001-evaluating-the-impact-of-code-duplication' / 'quickstart.md'
        assert quickstart_path.exists(), "Quickstart documentation not found"

    def test_quickstart_script_imports_correct_modules(self):
        """Test that quickstart validation imports correct modules."""
        from quickstart_validation import (
            validate_config_documentation,
            validate_directory_structure,
            validate_checksum_manifest,
            validate_quickstart_documentation,
            validate_output_files,
            validate_quickstart_steps,
            main,
        )

        # Verify all functions are callable
        assert callable(validate_config_documentation)
        assert callable(validate_directory_structure)
        assert callable(validate_checksum_manifest)
        assert callable(validate_quickstart_documentation)
        assert callable(validate_output_files)
        assert callable(validate_quickstart_steps)
        assert callable(main)
