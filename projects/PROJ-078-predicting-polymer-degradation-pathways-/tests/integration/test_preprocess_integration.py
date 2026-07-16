import pytest
from preprocess import preprocess_polymer_dataset
from data_models import PolymerRecord

class TestPreprocessPipelineIntegration:
    def test_full_pipeline_filters_correctly(self):
        """Test the full preprocessing pipeline filters correctly."""
        # Create a mix of records:
        # 1. Complete polyester (should pass)
        # 2. Incomplete polyester (missing temp - should fail)
        # 3. Complete non-polyester (should fail)
        # 4. Invalid SMILES (should fail)
        
        records = [
            # Valid polyester
            PolymerRecord(
                id="valid-polyester",
                smiles="CCOC(=O)C",
                temperature=25.0,
                ph=7.0,
                uv_intensity=10.0,
                degradation_pathway="hydrolysis"
            ),
            # Missing temperature
            PolymerRecord(
                id="missing-temp",
                smiles="CCOC(=O)C",
                temperature=None,
                ph=7.0,
                uv_intensity=10.0,
                degradation_pathway="hydrolysis"
            ),
            # Non-polyester
            PolymerRecord(
                id="non-polyester",
                smiles="CCCC",
                temperature=25.0,
                ph=7.0,
                uv_intensity=10.0,
                degradation_pathway="thermal"
            ),
            # Invalid SMILES
            PolymerRecord(
                id="invalid-smiles",
                smiles="GARBAGE",
                temperature=25.0,
                ph=7.0,
                uv_intensity=10.0,
                degradation_pathway="hydrolysis"
            )
        ]
        
        result = preprocess_polymer_dataset(records)
        
        # Only the valid polyester should remain
        assert len(result) == 1
        assert result[0].id == "valid-polyester"
        assert result[0].smiles == "CCOC(=O)C"

    def test_empty_input(self):
        """Test pipeline with empty input."""
        result = preprocess_polymer_dataset([])
        assert len(result) == 0

    def test_all_filtered(self):
        """Test pipeline where all records are filtered out."""
        records = [
            PolymerRecord(
                id="bad-1",
                smiles="CCCC",
                temperature=25.0,
                ph=7.0,
                uv_intensity=10.0,
                degradation_pathway="thermal"
            ),
            PolymerRecord(
                id="bad-2",
                smiles="CC",
                temperature=25.0,
                ph=7.0,
                uv_intensity=10.0,
                degradation_pathway="thermal"
            )
        ]
        result = preprocess_polymer_dataset(records)
        assert len(result) == 0
