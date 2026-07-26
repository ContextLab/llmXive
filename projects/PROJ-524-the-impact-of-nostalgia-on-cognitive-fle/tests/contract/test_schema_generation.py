import os
import yaml
import pytest
from pathlib import Path
import sys

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.schema_generator import generate_dataset_schema, generate_output_schema

class TestSchemaGeneration:
    def test_dataset_schema_structure(self):
        """Test that the dataset schema contains expected top-level keys and entities."""
        schema = generate_dataset_schema()
        
        assert "schema_name" in schema
        assert "entities" in schema
        assert "constraints" in schema
        
        # Check entities
        assert "participant" in schema["entities"]
        assert "cognitive_task" in schema["entities"]
        
        # Check fields exist
        participant_fields = [f["name"] for f in schema["entities"]["participant"]["fields"]]
        assert "participant_id" in participant_fields
        assert "age" in participant_fields
        assert "MMSE" in participant_fields

        cognitive_fields = [f["name"] for f in schema["entities"]["cognitive_task"]["fields"]]
        assert "stimulus_type" in cognitive_fields
        assert "perseverative_errors" in cognitive_fields

    def test_output_schema_structure(self):
        """Test that the output schema contains expected statistical fields."""
        schema = generate_output_schema()
        
        assert "schema_name" in schema
        assert "entities" in schema
        
        assert "statistical_comparison" in schema["entities"]
        assert "power_analysis" in schema["entities"]
        
        comp_fields = [f["name"] for f in schema["entities"]["statistical_comparison"]["fields"]]
        assert "t_statistic" in comp_fields
        assert "p_value" in comp_fields
        assert "cohens_d" in comp_fields
        
        power_fields = [f["name"] for f in schema["entities"]["power_analysis"]["fields"]]
        assert "observed_power" in power_fields
        assert "min_detectable_effect_size" in power_fields

    def test_yaml_serialization(self):
        """Test that schemas can be serialized to YAML without error."""
        dataset_schema = generate_dataset_schema()
        output_schema = generate_output_schema()
        
        try:
            yaml.dump(dataset_schema)
            yaml.dump(output_schema)
        except Exception as e:
            pytest.fail(f"Schema serialization failed: {e}")

    def test_contract_files_exist(self):
        """Verify that the contract files are generated and exist in the expected location."""
        # This test assumes the main() function has been run or the files are manually generated.
        # In a CI/CD context, we might run main() before this test.
        contracts_dir = Path("contracts")
        dataset_file = contracts_dir / "dataset.schema.yaml"
        output_file = contracts_dir / "output.schema.yaml"
        
        # If files don't exist, we can't test content, but we can check the directory structure logic
        # For this specific test, we assume the environment has run the generation or we skip if not present
        if not dataset_file.exists() or not output_file.exists():
            pytest.skip("Contract files not generated yet. Run code/schema_generator.py first.")

        with open(dataset_file, 'r') as f:
            loaded_dataset = yaml.safe_load(f)
            assert loaded_dataset is not None
            assert "entities" in loaded_dataset

        with open(output_file, 'r') as f:
            loaded_output = yaml.safe_load(f)
            assert loaded_output is not None
            assert "entities" in loaded_output
