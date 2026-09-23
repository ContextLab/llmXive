import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
from pathlib import Path
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hygiene import calculate_md5, load_artifact_hashes
from aggregate_clean import main as aggregate_main

class TestAggregateClean:
    @pytest.fixture
    def temp_project_structure(self):
        """Create a temporary project structure for testing."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir)
        
        # Create required directories
        (project_root / "code").mkdir()
        (project_root / "data" / "processed").mkdir(parents=True)
        (project_root / "state").mkdir()
        (project_root / "logs").mkdir()
        
        # Create a mock research.md (required by ingest)
        (project_root / "research.md").write_text("# Research Sources\n- https://openml.org/search?type=data&sort=runs&status=active&id=42\n")
        
        # Create a mock schema_map.json (required by ingest)
        config_dir = project_root / "config"
        config_dir.mkdir()
        (config_dir / "schema_map.json").write_text("{}")
        
        # Create a minimal seed.py
        (project_root / "code" / "seed.py").write_text("""
        def set_seed(s): pass
        def get_seed(): return 42
        def reset_seed(): pass
        def ensure_seed_set(): pass
        """)
        
        # Create a minimal logging_config.py
        (project_root / "code" / "logging_config.py").write_text("""
        import logging
        def setup_logging(): logging.basicConfig(level=logging.INFO)
        def get_logger(name): return logging.getLogger(name)
        def raise_on_missing_data(msg): raise ValueError(msg)
        """)
        
        # Create a mock ingest.py that generates a real CSV
        ingest_code = """
        import pandas as pd
        from pathlib import Path
        
        def main():
            # Generate a small real dataset to simulate T010-T014 output
            data = {
                'pulse_duration': [10.0, 20.0, 30.0],
                'power': [100.0, 150.0, 200.0],
                'scanning_speed': [500.0, 600.0, 700.0],
                'pattern_geometry': ['line', 'grid', 'hex'],
                'hardness': [500.0, 600.0, 700.0],
                'wear_rate': [0.1, 0.2, 0.15],
                'normalization_method': ['normalized', 'normalized', 'normalized']
            }
            df = pd.DataFrame(data)
            output_path = Path('data/processed/aggregated_clean.csv')
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
        """
        (project_root / "code" / "ingest.py").write_text(ingest_code)
        
        # Create a minimal hygiene.py for testing
        hygiene_code = """
        import hashlib
        import os
        from pathlib import Path
        from typing import Optional, Dict, Any
        import yaml
        from datetime import datetime

        def calculate_md5(file_path):
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()

        def get_file_metadata(file_path):
            stat = os.stat(file_path)
            return {
                'size_bytes': stat.st_size,
                'modified': str(datetime.fromtimestamp(stat.st_mtime))
            }

        def load_artifact_hashes(path):
            if not path.exists():
                return {}
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}

        def save_artifact_hashes(hashes, path):
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                yaml.safe_dump(hashes, f)

        def update_artifact_hash(hashes, key, hash_val, metadata):
            hashes[key] = {
                'hash': hash_val,
                'metadata': metadata
            }
        """
        (project_root / "code" / "hygiene.py").write_text(hygiene_code)

        yield project_root

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_aggregate_clean_creates_csv_and_hash(self, temp_project_structure):
        """
        Test that aggregate_clean.py:
        1. Runs the ingestion pipeline (mocked)
        2. Creates data/processed/aggregated_clean.csv
        3. Updates state/artifact_hashes.yaml with the checksum
        """
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        os.chdir(temp_project_structure)

        try:
            # Run the main function
            result = aggregate_main()
            
            assert result == 0, "aggregate_clean main() should return 0 on success"
            
            # Check 1: CSV file exists
            csv_path = Path("data/processed/aggregated_clean.csv")
            assert csv_path.exists(), "aggregated_clean.csv should be created"
            
            # Check 2: CSV has content
            df = pd.read_csv(csv_path)
            assert len(df) > 0, "CSV should not be empty"
            assert 'pulse_duration' in df.columns, "CSV should have expected columns"
            
            # Check 3: Hash file exists
            hash_path = Path("state/artifact_hashes.yaml")
            assert hash_path.exists(), "artifact_hashes.yaml should be created"
            
            # Check 4: Hash file contains the correct hash
            hashes = load_artifact_hashes(hash_path)
            expected_key = str(csv_path.relative_to(Path(".")))
            
            assert expected_key in hashes, f"Hash for {expected_key} should be in artifact_hashes.yaml"
            
            stored_hash = hashes[expected_key]['hash']
            actual_hash = calculate_md5(csv_path)
            
            assert stored_hash == actual_hash, "Stored hash should match actual file hash"
            
        finally:
            os.chdir(original_cwd)