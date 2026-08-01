import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.schemas import MicrobialTaxa, CognitiveScore, validate_microbial_data, validate_cognitive_data, export_schema_definitions
from code.utils import get_contracts_path

class TestMicrobialTaxaSchema:
    def test_valid_microbial_data(self):
        """Test valid microbial data passes validation"""
        data = [
            {"taxon_name": "Bacteroides fragilis", "relative_abundance": 0.15, "sample_id": "S001"},
            {"taxon_name": "Faecalibacterium prausnitzii", "relative_abundance": 0.08, "sample_id": "S002"}
        ]
        result = validate_microbial_data(data)
        assert len(result) == 2
        assert result[0].taxon_name == "Bacteroides fragilis"
        assert result[0].relative_abundance == 0.15
        assert result[0].sample_id == "S001"

    def test_invalid_relative_abundance_high(self):
        """Test that relative_abundance > 1.0 fails"""
        data = [
            {"taxon_name": "Bacteroides fragilis", "relative_abundance": 1.5, "sample_id": "S001"}
        ]
        with pytest.raises(ValueError):
            validate_microbial_data(data)

    def test_invalid_relative_abundance_negative(self):
        """Test that relative_abundance < 0.0 fails"""
        data = [
            {"taxon_name": "Bacteroides fragilis", "relative_abundance": -0.1, "sample_id": "S001"}
        ]
        with pytest.raises(ValueError):
            validate_microbial_data(data)

    def test_missing_required_field(self):
        """Test that missing required field fails"""
        data = [
            {"taxon_name": "Bacteroides fragilis", "relative_abundance": 0.15}
        ]
        with pytest.raises(ValueError):
            validate_microbial_data(data)

class TestCognitiveScoreSchema:
    def test_valid_cognitive_data(self):
        """Test valid cognitive data passes validation"""
        data = [
            {"task_type": "n-back", "z_score": 1.25, "participant_id": "P001"},
            {"task_type": "flanker", "z_score": -0.5, "participant_id": "P002"}
        ]
        result = validate_cognitive_data(data)
        assert len(result) == 2
        assert result[0].task_type == "n-back"
        assert result[0].z_score == 1.25
        assert result[0].participant_id == "P001"

    def test_invalid_z_score_type(self):
        """Test that non-numeric z_score fails"""
        data = [
            {"task_type": "n-back", "z_score": "high", "participant_id": "P001"}
        ]
        with pytest.raises(ValueError):
            validate_cognitive_data(data)

    def test_missing_required_field(self):
        """Test that missing required field fails"""
        data = [
            {"task_type": "n-back", "z_score": 1.25}
        ]
        with pytest.raises(ValueError):
            validate_cognitive_data(data)

class TestSchemaExport:
    def test_export_schema_creates_dict(self):
        """Test that export_schema_definitions returns a valid dict"""
        schema = export_schema_definitions()
        assert "MicrobialTaxa" in schema
        assert "CognitiveScore" in schema
        assert "MicrobialTaxa" in schema
        assert "properties" in schema["MicrobialTaxa"]
        assert "required" in schema["MicrobialTaxa"]

    def test_export_schema_creates_yaml_file(self, tmp_path):
        """Test that export_schema_definitions creates a YAML file"""
        output_file = tmp_path / "test_schema.yaml"
        export_schema_definitions(output_file)
        assert output_file.exists()
        
        import yaml
        with open(output_file, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert "MicrobialTaxa" in loaded
        assert "CognitiveScore" in loaded

    def test_schema_matches_requirements(self):
        """Test that schema contains all required fields per task T005"""
        schema = export_schema_definitions()
        
        # MicrobialTaxa requirements
        mt_props = schema["MicrobialTaxa"]["properties"]
        assert "taxon_name" in mt_props
        assert "relative_abundance" in mt_props
        assert "sample_id" in mt_props
        
        # CognitiveScore requirements
        cs_props = schema["CognitiveScore"]["properties"]
        assert "task_type" in cs_props
        assert "z_score" in cs_props
        assert "participant_id" in cs_props