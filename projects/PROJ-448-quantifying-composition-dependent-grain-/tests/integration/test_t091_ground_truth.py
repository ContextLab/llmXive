"""
Integration tests for T091: Generate Ground Truth

Tests that the ground truth generation script runs successfully
and produces valid output files with correct checksums.
"""
import os
import sys
import json
import hashlib
import tempfile
import shutil
import pytest
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import PROJECT_ROOT, DATA_RAW_DIR, RESEARCH_DIR

class TestT091GroundTruth:
    """Tests for ground truth generation."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup and teardown for each test."""
        # Save original paths
        self.original_data_raw = DATA_RAW_DIR
        self.original_research = RESEARCH_DIR
        
        # Create temporary directories
        self.temp_data = tmp_path / "data" / "raw"
        self.temp_research = tmp_path / "research"
        self.temp_data.mkdir(parents=True)
        self.temp_research.mkdir(parents=True)
        
        # Patch paths
        import code.config
        code.config.DATA_RAW_DIR = self.temp_data
        code.config.RESEARCH_DIR = self.temp_research
        
        yield
        
        # Restore original paths
        code.config.DATA_RAW_DIR = self.original_data_raw
        code.config.RESEARCH_DIR = self.original_research
    
    def test_synthetic_config_exists(self):
        """Test that synthetic ground truth config exists."""
        # Create a minimal config for testing
        config_path = self.temp_research / "synthetic_ground_truth.yaml"
        config_content = """
        random_seed: 42
        interaction_coefficients:
          beta_CrMo: 0.05
          beta_CrV: 0.03
          beta_MoV: 0.02
          beta_CrW: 0.04
          beta_MoW: 0.03
          beta_VW: 0.02
        """
        config_path.write_text(config_content)
        assert config_path.exists()
    
    def test_generate_ground_truth_script_runs(self):
        """Test that the ground truth generation script runs without errors."""
        # Ensure config exists
        config_path = self.temp_research / "synthetic_ground_truth.yaml"
        if not config_path.exists():
            config_content = """
            random_seed: 42
            interaction_coefficients:
              beta_CrMo: 0.05
              beta_CrV: 0.03
              beta_MoV: 0.02
              beta_CrW: 0.04
              beta_MoW: 0.03
              beta_VW: 0.02
            """
            config_path.write_text(config_content)
        
        # Run the script
        script_path = Path(__file__).parent.parent.parent / "data" / "generate_ground_truth.py"
        if script_path.exists():
            # Import and run main function
            from data.generate_ground_truth import main
            result = main()
            assert result == 0, "Script execution failed"
        else:
            pytest.skip("Script not found in test environment")
    
    def test_output_file_created(self):
        """Test that the output CSV file is created."""
        # Ensure config exists
        config_path = self.temp_research / "synthetic_ground_truth.yaml"
        if not config_path.exists():
            config_content = """
            random_seed: 42
            interaction_coefficients:
              beta_CrMo: 0.05
              beta_CrV: 0.03
              beta_MoV: 0.02
              beta_CrW: 0.04
              beta_MoW: 0.03
              beta_VW: 0.02
            """
            config_path.write_text(config_content)
        
        # Run the script
        from data.generate_ground_truth import main
        result = main()
        
        # Check output file
        output_path = self.temp_data / "generated_ground_truth.csv"
        assert output_path.exists(), "Output file was not created"
    
    def test_output_file_has_correct_columns(self):
        """Test that the output CSV has the correct columns."""
        # Ensure config exists
        config_path = self.temp_research / "synthetic_ground_truth.yaml"
        if not config_path.exists():
            config_content = """
            random_seed: 42
            interaction_coefficients:
              beta_CrMo: 0.05
              beta_CrV: 0.03
              beta_MoV: 0.02
              beta_CrW: 0.04
              beta_MoW: 0.03
              beta_VW: 0.02
            """
            config_path.write_text(config_content)
        
        # Run the script
        from data.generate_ground_truth import main
        main()
        
        # Load and check columns
        output_path = self.temp_data / "generated_ground_truth.csv"
        df = pd.read_csv(output_path)
        
        expected_columns = [
            'system', 'bulk_concentration', 'temperature_K',
            'segregation_energy_eV', 'equilibrium_concentration', 'is_saturated'
        ]
        
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"
    
    def test_output_file_has_data(self):
        """Test that the output CSV contains data."""
        # Ensure config exists
        config_path = self.temp_research / "synthetic_ground_truth.yaml"
        if not config_path.exists():
            config_content = """
            random_seed: 42
            interaction_coefficients:
              beta_CrMo: 0.05
              beta_CrV: 0.03
              beta_MoV: 0.02
              beta_CrW: 0.04
              beta_MoW: 0.03
              beta_VW: 0.02
            """
            config_path.write_text(config_content)
        
        # Run the script
        from data.generate_ground_truth import main
        main()
        
        # Load and check data
        output_path = self.temp_data / "generated_ground_truth.csv"
        df = pd.read_csv(output_path)
        
        assert len(df) > 0, "Output file is empty"
    
    def test_checksum_is_valid(self):
        """Test that the checksum in the manifest matches the file."""
        # Ensure config exists
        config_path = self.temp_research / "synthetic_ground_truth.yaml"
        if not config_path.exists():
            config_content = """
            random_seed: 42
            interaction_coefficients:
              beta_CrMo: 0.05
              beta_CrV: 0.03
              beta_MoV: 0.02
              beta_CrW: 0.04
              beta_MoW: 0.03
              beta_VW: 0.02
            """
            config_path.write_text(config_content)
        
        # Run the script
        from data.generate_ground_truth import main
        main()
        
        # Load manifest
        manifest_path = self.temp_data / "data_manifest.json"
        assert manifest_path.exists(), "Manifest file was not created"
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Find ground truth entry
        gt_entry = None
        for entry in manifest['entries']:
            if entry.get('source_id') == 'generate_ground_truth.py':
                gt_entry = entry
                break
        
        assert gt_entry is not None, "Ground truth entry not found in manifest"
        
        # Calculate actual checksum
        output_path = self.temp_data / "generated_ground_truth.csv"
        sha256_hash = hashlib.sha256()
        with open(output_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_checksum = sha256_hash.hexdigest()
        
        # Compare checksums
        assert gt_entry['checksum'] == actual_checksum, "Checksum mismatch"
    
    def test_reproducibility(self):
        """Test that running the script twice produces the same output."""
        # Ensure config exists
        config_path = self.temp_research / "synthetic_ground_truth.yaml"
        if not config_path.exists():
            config_content = """
            random_seed: 42
            interaction_coefficients:
              beta_CrMo: 0.05
              beta_CrV: 0.03
              beta_MoV: 0.02
              beta_CrW: 0.04
              beta_MoW: 0.03
              beta_VW: 0.02
            """
            config_path.write_text(config_content)
        
        # Run the script first time
        from data.generate_ground_truth import main
        main()
        
        # Read first output
        output_path = self.temp_data / "generated_ground_truth.csv"
        with open(output_path, 'r') as f:
            first_run = f.read()
        
        # Run the script second time
        main()
        
        # Read second output
        with open(output_path, 'r') as f:
            second_run = f.read()
        
        # Compare outputs
        assert first_run == second_run, "Outputs are not reproducible"