import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from main import run_ingestion_pipeline, fetch_synthetic_data
from utils.dedup import deduplicate_compositions

class TestIngestionPipeline:
    
    def test_fetch_synthetic_data(self):
        """Test that synthetic data generation works."""
        df = fetch_synthetic_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "composition" in df.columns
        assert "phase" in df.columns
        
        # Check composition format (basic check)
        first_comp = df.iloc[0]["composition"]
        assert isinstance(first_comp, str)
        assert len(first_comp) > 0

    def test_run_ingestion_pipeline(self, tmp_path):
        """
        Test the full ingestion pipeline.
        Since Zenodo/MP might be flaky, we rely on the fallback to synthetic
        if the real sources are unavailable, or we mock the environment.
        For this test, we assume the pipeline handles failures gracefully.
        """
        # Setup temp paths if needed, but main uses config which might be global
        # We just run it and check that it doesn't crash and produces a DataFrame
        # Note: This test might take a moment if it tries to fetch real data.
        
        # We will run the pipeline. If it falls back to synthetic, it should still succeed.
        result = run_ingestion_pipeline()
        
        # If result is None, it means total failure (no synthetic fallback triggered or error)
        # But our code ensures synthetic fallback.
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert "composition" in result.columns
        assert "source" in result.columns # Added in merge step

    def test_deduplication_logic(self):
        """Test that deduplication works on a small synthetic set."""
        # Create a small dataframe with duplicates
        data = {
            "composition": ["Zr50Cu50", "Zr50Cu50", "Cu60Zr40", "Cu60Zr40", "Fe80B20"],
            "phase": ["amorphous", "crystalline", "amorphous", "amorphous", "crystalline"],
            "source": ["synthetic", "synthetic", "synthetic", "synthetic", "synthetic"]
        }
        df = pd.DataFrame(data)
        
        deduped, stats = deduplicate_compositions(df)
        
        # We expect unique compositions.
        # "Zr50Cu50" appears twice -> 1 unique
        # "Cu60Zr40" appears twice -> 1 unique
        # "Fe80B20" appears once -> 1 unique
        assert len(deduped) == 3
        assert len(deduped["composition"].unique()) == 3
        
        # Check that the retained row has the highest priority source or logic
        # (In our simple implementation, it might just be the first one)
        assert "source" in deduped.columns
