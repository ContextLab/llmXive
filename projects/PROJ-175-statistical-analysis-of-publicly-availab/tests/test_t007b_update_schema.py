"""
Tests for T007b: Update Schema for Ratified Path.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import yaml
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.update_schema import update_schema, load_amendment_log, load_schema, save_schema

class TestUpdateSchema:
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            data_dir = tmp_path / "data"
            specs_dir = tmp_path / "specs" / "001-statistical-analysis-of-recipe-data" / "contracts"
            data_dir.mkdir(parents=True)
            specs_dir.mkdir(parents=True)
            yield tmp_path, data_dir, specs_dir

    def test_update_schema_correlational(self, temp_dirs):
        """Test schema update for Correlational Analysis."""
        _, _, specs_dir = temp_dirs
        schema_path = specs_dir / "dataset.schema.yaml"
        
        # Create initial schema
        initial_schema = {
            "properties": {
                "flavor_similarity": {
                    "description": "Placeholder"
                }
            }
        }
        with open(schema_path, 'w') as f:
            yaml.dump(initial_schema, f)
        
        # Load and update
        schema = load_schema()
        updated = update_schema(schema, "Correlational Analysis")
        
        assert updated['properties']['flavor_similarity']['description'] == "Recipe1M embedding cosine similarity"
        assert updated['properties']['flavor_similarity']['source'] == "Recipe1M"
        assert updated['properties']['flavor_similarity']['method'] == "cosine_similarity"

    def test_update_schema_causal(self, temp_dirs):
        """Test schema update for Causal Independence."""
        _, _, specs_dir = temp_dirs
        schema_path = specs_dir / "dataset.schema.yaml"
        
        # Create initial schema
        initial_schema = {
            "properties": {
                "flavor_similarity": {
                    "description": "Placeholder"
                }
            }
        }
        with open(schema_path, 'w') as f:
            yaml.dump(initial_schema, f)
        
        # Load and update
        schema = load_schema()
        updated = update_schema(schema, "Causal Independence")
        
        assert updated['properties']['flavor_similarity']['description'] == "FlavorDB chemical vectors"
        assert updated['properties']['flavor_similarity']['source'] == "FlavorDB"
        assert updated['properties']['flavor_similarity']['method'] == "chemical_vector_distance"

    def test_update_schema_missing_field(self, temp_dirs):
        """Test schema update when flavor_similarity field is missing."""
        _, _, specs_dir = temp_dirs
        schema_path = specs_dir / "dataset.schema.yaml"
        
        # Create schema without flavor_similarity
        initial_schema = {
            "properties": {
                "ingredient_id": {"type": "string"}
            }
        }
        with open(schema_path, 'w') as f:
            yaml.dump(initial_schema, f)
        
        # Load and update
        schema = load_schema()
        updated = update_schema(schema, "Correlational Analysis")
        
        assert 'flavor_similarity' in updated['properties']
        assert updated['properties']['flavor_similarity']['source'] == "Recipe1M"

    def test_update_schema_invalid_methodology(self, temp_dirs):
        """Test that invalid methodology raises error."""
        _, _, specs_dir = temp_dirs
        schema_path = specs_dir / "dataset.schema.yaml"
        
        initial_schema = {"properties": {}}
        with open(schema_path, 'w') as f:
            yaml.dump(initial_schema, f)
        
        schema = load_schema()
        
        with pytest.raises(ValueError, match="Unknown methodology"):
            update_schema(schema, "Invalid Methodology")

    def test_load_amendment_log_success(self, temp_dirs):
        """Test loading a valid ratified amendment log."""
        data_dir = temp_dirs[1]
        log_path = data_dir / "amendment_log.json"
        
        log_data = {
            "status": "RATIFIED",
            "methodology": "Correlational Analysis",
            "timestamp": "2023-10-01T00:00:00Z"
        }
        with open(log_path, 'w') as f:
            json.dump(log_data, f)
        
        # Temporarily override global path for testing
        import data.update_schema as mod
        original_path = mod.AMENDMENT_LOG_PATH
        mod.AMENDMENT_LOG_PATH = log_path
        
        try:
            result = load_amendment_log()
            assert result['status'] == 'RATIFIED'
            assert result['methodology'] == 'Correlational Analysis'
        finally:
            mod.AMENDMENT_LOG_PATH = original_path

    def test_load_amendment_log_not_ratified(self, temp_dirs):
        """Test that non-ratified log raises error."""
        data_dir = temp_dirs[1]
        log_path = data_dir / "amendment_log.json"
        
        log_data = {
            "status": "PENDING",
            "methodology": "Correlational Analysis"
        }
        with open(log_path, 'w') as f:
            json.dump(log_data, f)
        
        import data.update_schema as mod
        original_path = mod.AMENDMENT_LOG_PATH
        mod.AMENDMENT_LOG_PATH = log_path
        
        try:
            with pytest.raises(RuntimeError, match="expected 'RATIFIED'"):
                load_amendment_log()
        finally:
            mod.AMENDMENT_LOG_PATH = original_path

    def test_load_amendment_log_missing(self, temp_dirs):
        """Test that missing log raises error."""
        data_dir = temp_dirs[1]
        log_path = data_dir / "amendment_log.json"
        
        import data.update_schema as mod
        original_path = mod.AMENDMENT_LOG_PATH
        mod.AMENDMENT_LOG_PATH = log_path
        
        try:
            with pytest.raises(FileNotFoundError, match="Amendment log not found"):
                load_amendment_log()
        finally:
            mod.AMENDMENT_LOG_PATH = original_path

    def test_load_schema_missing(self, temp_dirs):
        """Test that missing schema raises error."""
        _, _, specs_dir = temp_dirs
        schema_path = specs_dir / "dataset.schema.yaml"
        
        import data.update_schema as mod
        original_path = mod.SCHEMA_PATH
        mod.SCHEMA_PATH = schema_path
        
        try:
            with pytest.raises(FileNotFoundError, match="Schema file not found"):
                load_schema()
        finally:
            mod.SCHEMA_PATH = original_path
