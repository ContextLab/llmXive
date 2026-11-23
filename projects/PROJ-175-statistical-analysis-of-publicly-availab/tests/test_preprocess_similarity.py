import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.preprocess import calculate_flavor_similarity, levenshtein_similarity

class TestSemanticSimilarity:
    def setup_method(self):
        """Setup test fixtures."""
        # Create a mock dataframe with embeddings
        self.mock_data = pd.DataFrame({
            "ingredient_id": [1, 2, 3, 4],
            "ingredient_name": ["salt", "pepper", "sugar", "flour"],
            "embedding": [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [0.5, 0.5, 0.0]
            ]
        })
        self.output_dir = Path("data/processed")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.test_output = self.output_dir / "test_flavor_similarity.parquet"
        self.test_log = self.output_dir / "test_flavor_similarity_log.json"

    def teardown_method(self):
        """Clean up test files."""
        if self.test_output.exists():
            self.test_output.unlink()
        if self.test_log.exists():
            self.test_log.unlink()

    def test_levenshtein_similarity(self):
        """Test Levenshtein similarity calculation."""
        assert levenshtein_similarity("salt", "salt") == 1.0
        assert levenshtein_similarity("salt", "saltz") > 0.5
        assert levenshtein_similarity("salt", "pepper") < 0.5

    def test_calculate_flavor_similarity(self):
        """Test the main similarity calculation function."""
        calculate_flavor_similarity(
            self.mock_data,
            str(self.test_output),
            str(self.test_log)
        )
        
        assert self.test_output.exists(), "Output file not created"
        assert self.test_log.exists(), "Log file not created"
        
        result = pd.read_parquet(self.test_output)
        
        # Check columns
        assert "ingredient_id_1" in result.columns
        assert "ingredient_id_2" in result.columns
        assert "flavor_similarity" in result.columns
        
        # Check values (orthogonal vectors should have 0 similarity)
        # salt (1,0,0) vs pepper (0,1,0) -> 0.0
        # salt (1,0,0) vs sugar (0,0,1) -> 0.0
        # pepper (0,1,0) vs sugar (0,0,1) -> 0.0
        # salt (1,0,0) vs flour (0.5,0.5,0) -> cos(45deg) = 0.707...
        
        # Verify specific pair
        salt_pepper = result[
            ((result["ingredient_id_1"] == 1) & (result["ingredient_id_2"] == 2)) |
            ((result["ingredient_id_1"] == 2) & (result["ingredient_id_2"] == 1))
        ]
        
        if len(salt_pepper) > 0:
            assert np.isclose(salt_pepper["flavor_similarity"].iloc[0], 0.0, atol=1e-5)

    def test_missing_embeddings(self):
        """Test handling of missing embeddings."""
        data_with_missing = self.mock_data.copy()
        data_with_missing.loc[0, "embedding"] = None
        
        # Should not raise, but exclude the row
        calculate_flavor_similarity(
            data_with_missing,
            str(self.test_output),
            str(self.test_log)
        )
        
        result = pd.read_parquet(self.test_output)
        # Should have fewer rows because one was excluded
        # Original 4 items -> 6 pairs. With 3 items -> 3 pairs.
        assert len(result) == 3

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        empty_df = pd.DataFrame(columns=["ingredient_id", "embedding"])
        
        with pytest.raises(ValueError, match="No valid embeddings found"):
            calculate_flavor_similarity(
                empty_df,
                str(self.test_output),
                str(self.test_log)
            )
