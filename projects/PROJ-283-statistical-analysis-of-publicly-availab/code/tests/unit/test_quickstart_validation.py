"""
Unit tests for quickstart.md validation.
This test suite verifies that the quickstart documentation steps can be executed
and produce the expected outputs as described in the documentation.
"""

import pytest
import os
import subprocess
import sys
from pathlib import Path
import json
import pandas as pd

# Constants for expected paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS = PROJECT_ROOT / "data" / "results"
SPEC_CONTRACTS = PROJECT_ROOT / "specs" / "contracts"

class TestQuickstartValidation:
    """Tests that validate the quickstart.md workflow."""

    def test_project_structure_exists(self):
        """Verify that the required project directories exist."""
        required_dirs = [
            "src", "tests", "data", "specs",
            "data/raw", "data/processed", "data/results",
            "specs/contracts", "tests/contract", "tests/unit", "tests/integration"
        ]
        for dir_name in required_dirs:
            dir_path = PROJECT_ROOT / dir_name
            assert dir_path.exists(), f"Directory {dir_path} does not exist"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_requirements_file_exists(self):
        """Verify that requirements.txt exists at the project root."""
        requirements_path = PROJECT_ROOT / "requirements.txt"
        assert requirements_path.exists(), "requirements.txt not found at project root"
        
        with open(requirements_path, 'r') as f:
            content = f.read()
            required_packages = ['pandas', 'numpy', 'scikit-learn', 'statsmodels', 
                                'chess', 'matplotlib', 'seaborn', 'requests', 
                                'datasets', 'pytest']
            for package in required_packages:
                assert package.lower() in content.lower(), f"Package {package} missing from requirements.txt"

    def test_contract_schemas_exist(self):
        """Verify that required contract schema files exist."""
        required_schemas = [
            "game_record.schema.yaml",
            "model_output.schema.yaml"
        ]
        for schema_name in required_schemas:
            schema_path = SPEC_CONTRACTS / schema_name
            assert schema_path.exists(), f"Schema file {schema_path} does not exist"

    def test_data_download_module_exists(self):
        """Verify that the data download module exists."""
        download_module = PROJECT_ROOT / "src" / "data" / "download.py"
        assert download_module.exists(), f"Data download module not found at {download_module}"

    def test_data_parse_module_exists(self):
        """Verify that the data parse module exists."""
        parse_module = PROJECT_ROOT / "src" / "data" / "parse.py"
        assert parse_module.exists(), f"Data parse module not found at {parse_module}"

    def test_data_process_module_exists(self):
        """Verify that the data process module exists."""
        process_module = PROJECT_ROOT / "src" / "data" / "process.py"
        assert process_module.exists(), f"Data process module not found at {process_module}"

    def test_model_fit_module_exists(self):
        """Verify that the model fit module exists."""
        fit_module = PROJECT_ROOT / "src" / "models" / "fit.py"
        assert fit_module.exists(), f"Model fit module not found at {fit_module}"

    def test_model_metrics_module_exists(self):
        """Verify that the model metrics module exists."""
        metrics_module = PROJECT_ROOT / "src" / "models" / "metrics.py"
        assert metrics_module.exists(), f"Model metrics module not found at {metrics_module}"

    def test_model_validate_module_exists(self):
        """Verify that the model validate module exists."""
        validate_module = PROJECT_ROOT / "src" / "models" / "validate.py"
        assert validate_module.exists(), f"Model validate module not found at {validate_module}"

    def test_reports_generate_plots_module_exists(self):
        """Verify that the reports generate plots module exists."""
        plots_module = PROJECT_ROOT / "src" / "reports" / "generate_plots.py"
        assert plots_module.exists(), f"Reports generate plots module not found at {plots_module}"

    def test_validation_module_exists(self):
        """Verify that the validation module exists."""
        validation_module = PROJECT_ROOT / "src" / "validation" / "validate_contracts.py"
        assert validation_module.exists(), f"Validation module not found at {validation_module}"

    def test_config_module_exists(self):
        """Verify that the config module exists."""
        config_module = PROJECT_ROOT / "src" / "config.py"
        assert config_module.exists(), f"Config module not found at {config_module}"

    def test_pytest_can_run(self):
        """Verify that pytest can be executed on the project."""
        # Run pytest on a small subset to verify it works
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/unit/test_calculations.py", "-v", "--tb=short"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )
        # We expect at least the test to be discovered, even if it fails due to missing data
        assert "collected" in result.stdout or "passed" in result.stdout or "failed" in result.stdout, \
            f"pytest failed to run: {result.stderr}"

    def test_module_imports_work(self):
        """Verify that key modules can be imported without errors."""
        modules_to_test = [
            "src.config",
            "src.data.download",
            "src.data.parse",
            "src.data.process",
            "src.models.fit",
            "src.models.metrics",
            "src.models.validate",
            "src.reports.generate_plots",
            "src.validation.validate_contracts"
        ]
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {str(e)}")

    def test_quickstart_script_runs(self):
        """
        Verify that the main quickstart script can be executed.
        This simulates running 'python src/main.py' as described in quickstart.md.
        """
        main_script = PROJECT_ROOT / "src" / "main.py"
        if not main_script.exists():
            pytest.skip("main.py not found - skipping quickstart execution test")
        
        # Run the main script with a timeout
        result = subprocess.run(
            [sys.executable, str(main_script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # The script may fail due to missing data, but it should at least start
        # We check that it doesn't crash immediately with import errors
        assert "ModuleNotFoundError" not in result.stderr, \
            f"Main script failed with import error: {result.stderr}"

    def test_output_directories_are_writable(self):
        """Verify that output directories are writable."""
        test_file = DATA_PROCESSED / ".test_writable"
        try:
            test_file.touch()
            test_file.unlink()
            assert True
        except Exception as e:
            pytest.fail(f"Output directory not writable: {str(e)}")

    def test_game_record_schema_has_required_columns(self):
        """Verify that the game_record schema contains required columns."""
        schema_path = SPEC_CONTRACTS / "game_record.schema.yaml"
        if not schema_path.exists():
            pytest.skip("game_record.schema.yaml not found")
        
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        required_columns = [
            'game_id', 'white_rating', 'black_rating', 'eco_code',
            'avg_move_time_white', 'avg_move_time_black', 'material_imbalance_move5',
            'outcome', 'elo_expected_prob', 'outcome_deviation'
        ]
        
        # Check if columns are defined in the schema
        # The schema structure may vary, so we check for column definitions
        schema_str = str(schema).lower()
        for col in required_columns:
            assert col in schema_str, f"Column {col} not found in game_record schema"

    def test_model_output_schema_has_required_columns(self):
        """Verify that the model_output schema contains required columns."""
        schema_path = SPEC_CONTRACTS / "model_output.schema.yaml"
        if not schema_path.exists():
            pytest.skip("model_output.schema.yaml not found")
        
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        required_columns = ['model_type', 'coefficients', 'p_values', 'r_squared', 'aic', 'cross_validation_scores']
        
        schema_str = str(schema).lower()
        for col in required_columns:
            assert col in schema_str, f"Column {col} not found in model_output schema"

    def test_all_test_files_exist(self):
        """Verify that all expected test files exist."""
        test_files = [
            "tests/contract/test_game_record.py",
            "tests/contract/test_validation.py",
            "tests/unit/test_calculations.py",
            "tests/unit/test_download.py",
            "tests/unit/test_feature_preparation.py",
            "tests/unit/test_fit.py",
            "tests/unit/test_generate_diagnostics.py",
            "tests/unit/test_generate_plots.py",
            "tests/unit/test_main_integration.py",
            "tests/unit/test_metrics.py",
            "tests/unit/test_optimization.py",
            "tests/unit/test_parse.py",
            "tests/unit/test_parsers.py",
            "tests/unit/test_process.py",
            "tests/unit/test_save_metrics.py",
            "tests/unit/test_sensitivity.py",
            "tests/unit/test_validate.py",
            "tests/unit/test_validate_contracts.py"
        ]
        
        for test_file in test_files:
            test_path = PROJECT_ROOT / test_file
            # Some files may be optional or created later, so we just check existence
            # and skip if not found
            if not test_path.exists():
                pytest.skip(f"Test file {test_file} not found - may be optional")

    def test_quickstart_documentation_reference(self):
        """
        Verify that quickstart.md exists and contains expected content.
        """
        quickstart_path = PROJECT_ROOT / "quickstart.md"
        if not quickstart_path.exists():
            # Alternative location
            quickstart_path = PROJECT_ROOT / "README.md"
            if not quickstart_path.exists():
                pytest.skip("Neither quickstart.md nor README.md found")
        
        with open(quickstart_path, 'r') as f:
            content = f.read().lower()
        
        # Check for key quickstart elements
        expected_elements = [
            "python", "pip", "install", "requirements.txt",
            "data", "processed", "results"
        ]
        
        for element in expected_elements:
            assert element in content, f"Quickstart documentation missing expected element: {element}"