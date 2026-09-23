import os
import sys
import yaml
import hashlib
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from hygiene import calculate_md5, load_artifact_hashes
from generate_artifacts import main as t015_main

class TestT015Artifacts:
    """
    Tests for T015: Generate aggregated_clean.csv and update artifact_hashes.yaml.
    """

    @pytest.fixture
    def temp_project_structure(self):
        """Create a temporary project structure with mock data."""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        
        # Create directory structure
        data_processed = temp_path / "data" / "processed"
        state_dir = temp_path / "state"
        code_dir = temp_path / "code"
        
        data_processed.mkdir(parents=True, exist_ok=True)
        state_dir.mkdir(parents=True, exist_ok=True)
        code_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a mock aggregated_clean.csv
        mock_data = {
            'pulse_duration': [10.0, 20.0, 30.0],
            'power': [100.0, 150.0, 200.0],
            'scanning_speed': [5.0, 10.0, 15.0],
            'pattern_geometry': ['dot', 'line', 'grid'],
            'hardness': [500.0, 600.0, 700.0],
            'wear_rate': [0.01, 0.02, 0.03],
            'normalization_method': ['archard', 'archard', 'raw']
        }
        df = pd.DataFrame(mock_data)
        csv_path = data_processed / "aggregated_clean.csv"
        df.to_csv(csv_path, index=False)
        
        yield {
            'root': temp_path,
            'csv_path': csv_path,
            'state_dir': state_dir,
            'hash_file': state_dir / "artifact_hashes.yaml"
        }
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_t015_generates_hash_file(self, temp_project_structure):
        """Test that T015 creates the artifact_hashes.yaml file."""
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        os.chdir(temp_project_structure['root'])
        
        try:
            # Run T015 main
            t015_main()
            
            hash_file = temp_project_structure['hash_file']
            assert hash_file.exists(), "artifact_hashes.yaml was not created"
            
            # Verify content is valid YAML
            with open(hash_file, 'r') as f:
                content = yaml.safe_load(f)
            
            assert content is not None, "artifact_hashes.yaml is empty"
            assert 'artifacts' in content, "Missing 'artifacts' key in YAML"
            
            # Check that our CSV is registered
            csv_path = str(temp_project_structure['csv_path'])
            found = False
            for artifact in content['artifacts']:
                if artifact.get('path') == csv_path:
                    found = True
                    assert 'md5' in artifact, "Missing 'md5' for artifact"
                    # Verify MD5 is correct
                    expected_md5 = calculate_md5(csv_path)
                    assert artifact['md5'] == expected_md5, "MD5 mismatch"
                    break
            
            assert found, f"Artifact {csv_path} not found in hashes file"
            
        finally:
            os.chdir(original_cwd)

    def test_t015_fails_on_missing_input(self, temp_project_structure):
        """Test that T015 fails gracefully if input file is missing."""
        # Remove the input file
        temp_project_structure['csv_path'].unlink()
        
        original_cwd = os.getcwd()
        os.chdir(temp_project_structure['root'])
        
        try:
            with pytest.raises(FileNotFoundError):
                t015_main()
        finally:
            os.chdir(original_cwd)

    def test_t015_fails_on_empty_input(self, temp_project_structure):
        """Test that T015 fails if input file is empty."""
        # Create an empty file
        temp_project_structure['csv_path'].write_text("")
        
        original_cwd = os.getcwd()
        os.chdir(temp_project_structure['root'])
        
        try:
            with pytest.raises(ValueError):
                t015_main()
        finally:
            os.chdir(original_cwd)