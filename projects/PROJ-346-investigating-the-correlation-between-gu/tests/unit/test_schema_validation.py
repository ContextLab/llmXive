import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas import MicrobialTaxa, CognitiveScore, validate_microbial_data, validate_cognitive_data
from code.utils import get_contracts_path

class TestMicrobialTaxaSchema:
    def test_valid_microbial_data(self):
        """Test validation of valid microbial data"""
        df = pd.DataFrame({
            'taxon_name': ['Bacteroides', 'Firmicutes'],
            'relative_abundance': [0.45, 0.32],
            'sample_id': ['S001', 'S002']
        })
        assert validate_microbial_data(df) is True

    def test_invalid_taxon_name_empty(self):
        """Test validation fails with empty taxon_name"""
        df = pd.DataFrame({
            'taxon_name': ['', 'Firmicutes'],
            'relative_abundance': [0.45, 0.32],
            'sample_id': ['S001', 'S002']
        })
        with pytest.raises(ValueError):
            validate_microbial_data(df)

    def test_invalid_abundance_range(self):
        """Test validation fails with abundance outside 0-1"""
        df = pd.DataFrame({
            'taxon_name': ['Bacteroides'],
            'relative_abundance': [1.5],
            'sample_id': ['S001']
        })
        with pytest.raises(ValueError):
            validate_microbial_data(df)

    def test_missing_columns(self):
        """Test validation fails with missing required columns"""
        df = pd.DataFrame({
            'taxon_name': ['Bacteroides'],
            'relative_abundance': [0.45]
        })
        with pytest.raises(ValueError):
            validate_microbial_data(df)

class TestCognitiveScoreSchema:
    def test_valid_cognitive_data(self):
        """Test validation of valid cognitive data"""
        df = pd.DataFrame({
            'task_type': ['Memory', 'Attention'],
            'z_score': [1.2, -0.5],
            'participant_id': ['P001', 'P002']
        })
        assert validate_cognitive_data(df) is True

    def test_invalid_task_type_empty(self):
        """Test validation fails with empty task_type"""
        df = pd.DataFrame({
            'task_type': ['', 'Attention'],
            'z_score': [1.2, -0.5],
            'participant_id': ['P001', 'P002']
        })
        with pytest.raises(ValueError):
            validate_cognitive_data(df)

    def test_invalid_z_score_type(self):
        """Test validation fails with non-numeric z_score"""
        df = pd.DataFrame({
            'task_type': ['Memory'],
            'z_score': ['invalid'],
            'participant_id': ['P001']
        })
        with pytest.raises(ValueError):
            validate_cognitive_data(df)

    def test_missing_columns(self):
        """Test validation fails with missing required columns"""
        df = pd.DataFrame({
            'task_type': ['Memory'],
            'z_score': [1.2]
        })
        with pytest.raises(ValueError):
            validate_cognitive_data(df)

class TestSchemaFile:
    def test_schema_file_exists(self):
        """Test that the schema YAML file exists"""
        contracts_path = get_contracts_path()
        schema_file = contracts_path / "dataset.schema.yaml"
        assert schema_file.exists(), f"Schema file not found at {schema_file}"

    def test_schema_file_valid_yaml(self):
        """Test that the schema file is valid YAML"""
        import yaml
        contracts_path = get_contracts_path()
        schema_file = contracts_path / "dataset.schema.yaml"
        
        with open(schema_file, 'r') as f:
            schema = yaml.safe_load(f)
        
        assert 'MicrobialTaxa' in schema
        assert 'CognitiveScore' in schema
        assert 'fields' in schema['MicrobialTaxa']
        assert 'fields' in schema['CognitiveScore']