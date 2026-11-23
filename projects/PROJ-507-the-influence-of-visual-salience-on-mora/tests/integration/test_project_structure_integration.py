import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from project_setup import create_project_structure

class TestProjectStructureIntegration:
    """Integration tests for full project structure setup."""

    def test_full_pipeline_structure_exists(self):
        """
        Integration test: Verify the complete directory structure required
        by the pipeline exists after running project_setup.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Execute setup
                create_project_structure()
                
                # Verify all critical paths for the pipeline
                critical_paths = {
                    # Source code
                    "code": "Source code directory",
                    "code/config.py": "Configuration module",
                    "code/models.py": "Data models",
                    "code/data_prep.py": "Data preparation",
                    "code/analysis.py": "Analysis engine",
                    
                    # Data directories
                    "data/raw": "Raw external data",
                    "data/processed": "Processed data",
                    "data/survey": "Survey responses",
                    "data/synth": "Synthetic data (separated)",
                    "data/raw/human_coding": "Human coding annotations",
                    
                    # Testing
                    "tests": "Test suite root",
                    "tests/unit": "Unit tests",
                    "tests/integration": "Integration tests",
                    
                    # Output
                    "figures": "Generated plots",
                    "config": "Configuration files",
                    "docs": "Documentation",
                }
                
                for path, description in critical_paths.items():
                    full_path = Path(tmpdir) / path
                    assert full_path.exists(), f"Missing: {path} ({description})"
                    if not path.endswith(".py"):
                        assert full_path.is_dir(), f"Not a directory: {path} ({description})"
                
            finally:
                os.chdir(original_cwd)

    def test_structure_supports_task_requirements(self):
        """
        Integration test: Verify the structure supports specific task requirements
        mentioned in tasks.md (e.g., T013 output paths, T023b config paths).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                create_project_structure()
                
                # T013: data/processed/stimuli_raw.csv
                # T014: data/processed/validated_candidates.csv
                assert Path("data/processed").is_dir()
                
                # T015c: data/raw/human_coding/
                assert Path("data/raw/human_coding").is_dir()
                
                # T023b: config/survey_api.yaml
                assert Path("config").is_dir()
                
                # T026b: data/survey vs data/synth separation
                assert Path("data/survey").is_dir()
                assert Path("data/synth").is_dir()
                
                # T037: data/analysis/results.json (needs data/ or similar)
                # Note: data/analysis might be created later or under data/processed
                # For now, verify data/processed exists for analysis outputs
                assert Path("data/processed").is_dir()
                
            finally:
                os.chdir(original_cwd)

    def test_idempotency(self):
        """
        Integration test: Verify that running setup multiple times
        does not corrupt the structure or cause errors.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Run setup 3 times
                for i in range(3):
                    result = create_project_structure()
                    assert result is True
                    
                    # Verify structure still valid
                    assert Path("code").is_dir()
                    assert Path("data/processed").is_dir()
                    assert Path("tests/unit").is_dir()
                    
            finally:
                os.chdir(original_cwd)
