"""Platform compatibility tests for Linux/GitHub Actions environment.

These tests validate that the codebase runs correctly on the Linux platform
as used in GitHub Actions CI/CD pipelines.
"""
import sys
import os
import platform
import pytest
from pathlib import Path


class TestLinuxPlatformCompatibility:
    """Validate Linux-specific platform compatibility."""

    def test_python_version_on_linux(self):
        """Verify Python 3.11 is available on Linux platform."""
        assert sys.version_info.major == 3
        assert sys.version_info.minor >= 10
        assert sys.version_info.minor <= 12

    def test_linux_platform_detection(self):
        """Verify we can detect Linux platform."""
        # On GitHub Actions ubuntu-latest, platform.system() returns 'Linux'
        assert platform.system() == 'Linux'

    def test_project_structure_exists(self):
        """Verify project directory structure exists."""
        project_root = Path(__file__).parent.parent.parent
        assert project_root.exists()

        # Check required directories
        assert (project_root / 'code').exists()
        assert (project_root / 'data').exists()
        assert (project_root / 'tests').exists()

    def test_requirements_file_exists(self):
        """Verify requirements.txt exists for dependency installation."""
        project_root = Path(__file__).parent.parent.parent
        requirements_path = project_root / 'requirements.txt'
        assert requirements_path.exists()

    def test_import_core_modules(self):
        """Verify core modules can be imported on Linux."""
        # Test imports from existing API surface
        try:
            from config import get_clone_thresholds, get_random_seed
            assert callable(get_clone_thresholds)
            assert callable(get_random_seed)
        except ImportError as e:
            pytest.fail(f"Failed to import config module: {e}")

    def test_import_data_loader(self):
        """Verify data_loader can be imported."""
        try:
            from data_loader import load_raw_data
            assert callable(load_raw_data)
        except ImportError as e:
            pytest.fail(f"Failed to import data_loader module: {e}")

    def test_import_model_metrics(self):
        """Verify model_metrics can be imported."""
        try:
            from model_metrics import load_model_and_tokenizer, compute_perplexity
            assert callable(load_model_and_tokenizer)
            assert callable(compute_perplexity)
        except ImportError as e:
            pytest.fail(f"Failed to import model_metrics module: {e}")

    def test_import_bug_detection(self):
        """Verify bug_detection can be imported."""
        try:
            from bug_detection import load_humaneval_dataset, compute_pass1_accuracy
            assert callable(load_humaneval_dataset)
            assert callable(compute_pass1_accuracy)
        except ImportError as e:
            pytest.fail(f"Failed to import bug_detection module: {e}")

    def test_import_correlation_analysis(self):
        """Verify correlation_analysis can be imported."""
        try:
            from correlation_analysis import calculate_correlation, sensitivity_analysis
            assert callable(calculate_correlation)
        except ImportError as e:
            pytest.fail(f"Failed to import correlation_analysis module: {e}")

    def test_import_visualization(self):
        """Verify visualization can be imported."""
        try:
            from visualization import create_scatter_plot_with_regression
            assert callable(create_scatter_plot_with_regression)
        except ImportError as e:
            pytest.fail(f"Failed to import visualization module: {e}")

    def test_file_encoding_utf8(self):
        """Verify files can be read with UTF-8 encoding on Linux."""
        project_root = Path(__file__).parent.parent.parent
        readme_path = project_root / 'README.md'
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert isinstance(content, str)

    def test_path_separators(self):
        """Verify pathlib handles path separators correctly on Linux."""
        test_path = Path('code') / 'config.py'
        assert '/' in str(test_path) or os.sep in str(test_path)

    def test_temp_directory_writable(self):
        """Verify temp directory is writable (important for CI)."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / 'test.txt'
            test_file.write_text('test')
            assert test_file.exists()

    def test_network_modules_available(self):
        """Verify network-related modules are available."""
        try:
            import urllib.request
            import http.client
        except ImportError as e:
            pytest.fail(f"Network modules not available: {e}")

    def test_json_module_available(self):
        """Verify JSON module is available for data serialization."""
        import json
        test_data = {'test': 'value', 'number': 42}
        serialized = json.dumps(test_data)
        deserialized = json.loads(serialized)
        assert deserialized == test_data

    def test_csv_module_available(self):
        """Verify CSV module is available for data handling."""
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['col1', 'col2'])
        writer.writerow(['val1', 'val2'])
        assert 'col1' in output.getvalue()

    def test_logging_module_available(self):
        """Verify logging module is available."""
        import logging
        logger = logging.getLogger('test_logger')
        assert logger is not None

    def test_numpy_available(self):
        """Verify numpy is available for numerical operations."""
        try:
            import numpy as np
            arr = np.array([1, 2, 3])
            assert len(arr) == 3
        except ImportError:
            pytest.skip("numpy not installed")

    def test_pandas_available(self):
        """Verify pandas is available for data manipulation."""
        try:
            import pandas as pd
            df = pd.DataFrame({'a': [1, 2, 3]})
            assert len(df) == 3
        except ImportError:
            pytest.skip("pandas not installed")

    def test_matplotlib_available(self):
        """Verify matplotlib is available for visualization."""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend for CI
            import matplotlib.pyplot as plt
            assert plt is not None
        except ImportError:
            pytest.skip("matplotlib not installed")

    def test_ast_module_available(self):
        """Verify ast module is available for code parsing."""
        import ast
        code = "x = 1"
        tree = ast.parse(code)
        assert tree is not None

    def test_subprocess_module_available(self):
        """Verify subprocess module is available for running commands."""
        import subprocess
        result = subprocess.run(['echo', 'test'], capture_output=True, text=True)
        assert result.returncode == 0

    def test_threading_module_available(self):
        """Verify threading module is available for concurrent operations."""
        import threading
        assert threading.Thread is not None

    def test_pathlib_operations(self):
        """Verify pathlib Path operations work correctly."""
        test_path = Path('/tmp') / 'test_file.txt'
        assert test_path.parent == Path('/tmp')
        assert test_path.name == 'test_file.txt'
        assert test_path.suffix == '.txt'

    def test_datetime_operations(self):
        """Verify datetime module works correctly."""
        from datetime import datetime
        now = datetime.now()
        assert now.year >= 2020

    def test_hashlib_available(self):
        """Verify hashlib is available for checksums."""
        import hashlib
        checksum = hashlib.sha256(b'test').hexdigest()
        assert len(checksum) == 64

    def test_threading_lock_available(self):
        """Verify threading Lock is available."""
        import threading
        lock = threading.Lock()
        assert lock is not None

    def test_contextlib_available(self):
        """Verify contextlib is available."""
        from contextlib import contextmanager
        @contextmanager
        def test_context():
            yield
        assert test_context is not None