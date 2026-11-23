"""
Test suite for validating the quickstart.md end-to-end pipeline on a small batch.
This test ensures that the pipeline runs correctly on a subset of data and produces
the expected artifacts without errors.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.logging_config import setup_logging
from utils.validators import enforce_2d_only_imports
from data.loader import iterate_smiles
from data.preprocess_2d import compute_descriptors_batch


class TestQuickStartValidation:
    """Tests for validating the quickstart pipeline on a small batch."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test environment with temporary directories."""
        self.tmp_path = tmp_path
        self.data_dir = tmp_path / 'data'
        self.data_dir.mkdir()
        self.raw_dir = self.data_dir / 'raw'
        self.processed_dir = self.data_dir / 'processed'
        self.logs_dir = tmp_path / 'logs'
        self.raw_dir.mkdir()
        self.processed_dir.mkdir()
        self.logs_dir.mkdir()

        # Create a small test SMILES file
        self.test_smiles_file = self.raw_dir / 'test_smiles.csv'
        with open(self.test_smiles_file, 'w') as f:
            f.write("smiles,target\n")
            f.write("CCO,0.5\n")  # Ethanol
            f.write("CC(=O)O,1.2\n")  # Acetic acid
            f.write("C1=CC=CC=C1,0.0\n")  # Benzene
            f.write("CCN(CC)CC,0.8\n")  # Triethylamine
            f.write("C1CCCCC1,0.1\n")  # Cyclohexane
            f.write("CC(C)C,0.3\n")  # Isobutane
            f.write("C1=CC=C(O)C=C1,0.6\n")  # Phenol
            f.write("CC#N,0.4\n")  # Acetonitrile
            f.write("CC(=O)NC,0.7\n")  # Acetamide
            f.write("C1CC1,0.2\n")  # Cyclopropane

        # Setup logging for tests
        setup_logging(log_file=str(self.logs_dir / 'test.log'))

    def test_environment_setup(self):
        """Test that all required dependencies are installed."""
        required_packages = ['rdkit', 'lightgbm', 'pandas', 'numpy', 'shap', 'pyyaml', 'pytest']
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                pytest.fail(f"Required package '{package}' is not installed.")

    def test_data_loader_validation(self):
        """Test that the data loader correctly processes SMILES strings."""
        smiles_list = list(iterate_smiles(str(self.test_smiles_file)))
        assert len(smiles_list) == 10, f"Expected 10 SMILES, got {len(smiles_list)}"
        for smiles, target in smiles_list:
            assert isinstance(smiles, str), "SMILES should be a string"
            assert isinstance(target, float), "Target should be a float"

    def test_descriptor_computation(self):
        """Test that descriptors are computed correctly for a small batch."""
        output_file = self.processed_dir / 'test_descriptors.parquet'
        result = compute_descriptors_batch(
            input_path=str(self.test_smiles_file),
            output_path=str(output_file),
            batch_size=5
        )

        assert output_file.exists(), "Output file should exist"
        df = pd.read_parquet(output_file)
        assert 'smiles' in df.columns, "Output should contain 'smiles' column"
        assert 'target' in df.columns, "Output should contain 'target' column"
        assert len(df) == 10, f"Expected 10 rows, got {len(df)}"

        # Verify no 3D/TPSA descriptors
        for col in df.columns:
            assert 'TPSA' not in col, f"TPSA descriptor found in column: {col}"

    def test_logging_configuration(self):
        """Test that logging is configured correctly."""
        from utils.logging_config import get_logger
        logger = get_logger('test_logger')
        logger.info("Test log message")

        log_file = self.logs_dir / 'test.log'
        assert log_file.exists(), "Log file should exist"

        with open(log_file, 'r') as f:
            log_content = f.read()
            assert "Test log message" in log_content, "Log message should be in log file"

    def test_2d_only_enforcement(self):
        """Test that 3D calls are properly enforced."""
        # This test verifies that the validator functions exist and work
        from utils.validators import enforce_2d_only_imports, assert_no_3d_calls

        # Create a mock module with 2D-only functions
        class MockModule:
            def Compute2DDescriptors(self):
                pass

        mock_module = MockModule()
        enforce_2d_only_imports(mock_module)

        # Test that 3D calls would be caught
        with pytest.raises(AssertionError):
            def mock_3d_call():
                from rdkit.Chem import AllChem
                AllChem.EmbedMolecule(None)
            assert_no_3d_calls(mock_3d_call)

    def test_pipeline_execution(self):
        """Test that the full pipeline executes without errors on a small batch."""
        # Run the main pipeline script with small batch size
        result = subprocess.run(
            [
                sys.executable,
                'code/main.py',
                '--batch-size', '5',
                '--skip-training',
                '--data-dir', str(self.data_dir),
                '--processed-dir', str(self.processed_dir),
                '--logs-dir', str(self.logs_dir)
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )

        # Check for successful execution
        assert result.returncode == 0, f"Pipeline failed with error: {result.stderr}"
        assert "Pipeline completed successfully" in result.stdout or "Pipeline completed successfully" in result.stderr

        # Verify output files exist
        descriptors_file = self.processed_dir / 'descriptors.parquet'
        assert descriptors_file.exists(), "Descriptors file should be created"

        correlation_file = self.processed_dir / 'correlation_matrix.csv'
        assert correlation_file.exists(), "Correlation matrix file should be created"

    def test_quickstart_guide_commands(self):
        """Test that commands from quickstart.md execute successfully."""
        # Test dependency check command
        result = subprocess.run(
            [sys.executable, '-c',
             'import rdkit; import lightgbm; import pandas; import numpy; import shap; import yaml; import pytest; print("All dependencies installed.")'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Dependency check failed"
        assert "All dependencies installed." in result.stdout

        # Test data validation command
        output_file = self.processed_dir / 'descriptors.parquet'
        if output_file.exists():
            result = subprocess.run(
                [sys.executable, '-c',
                 f'import pandas as pd; df = pd.read_parquet("{output_file}"); print(f"Shape: {df.shape}"); assert "smiles" in df.columns; assert "target" in df.columns'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, "Data validation failed"
            assert "Shape:" in result.stdout

        # Test 3D exclusion check
        if output_file.exists():
            result = subprocess.run(
                [sys.executable, '-c',
                 f'import pandas as pd; df = pd.read_parquet("{output_file}"); assert not any("TPSA" in col for col in df.columns), "TPSA found in output"; print("No 3D/TPSA descriptors found.")'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, "3D exclusion check failed"
            assert "No 3D/TPSA descriptors found." in result.stdout
