import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_ingestion import ingest_with_chunking, calculate_ratio_score, handle_fallback

class TestChunkedIngestion:
    def test_chunking_logic(self, tmp_path):
        """Test that ingest_with_chunking correctly processes a file in chunks."""
        # Create a synthetic large-ish file
        file_path = tmp_path / "test_data.tsv"
        rows = 500
        data = {
            "track_id": [f"TR{i}" for i in range(rows)],
            "year": [2000 + (i % 20) for i in range(rows)],
            "listen_count": [100 for _ in range(rows)]
        }
        df_sample = pd.DataFrame(data)
        df_sample.to_csv(file_path, sep='\t', index=False)
        
        # Run ingestion
        result = ingest_with_chunking(file_path, chunk_size=100)
        
        assert len(result) == rows
        assert "track_id" in result.columns
        assert "year" in result.columns

    def test_large_file_simulation(self, tmp_path):
        """Simulate a large file to ensure chunking is triggered."""
        file_path = tmp_path / "large_data.tsv"
        rows = 10000
        data = {
            "track_id": [f"TR{i}" for i in range(rows)],
            "year": [2000 for _ in range(rows)],
            "listen_count": [50 for _ in range(rows)]
        }
        df_large = pd.DataFrame(data)
        df_large.to_csv(file_path, sep='\t', index=False)
        
        result = ingest_with_chunking(file_path, chunk_size=5000)
        assert len(result) == rows
        assert result["track_id"].iloc[0] == "TR0"

class TestRatioScore:
    def test_ratio_calculation(self):
        """Test that adolescent exposure ratio is calculated correctly."""
        data = {
            "track_id": ["T1", "T1", "T1", "T2", "T2"],
            "is_adolescent_listen": [True, False, True, False, False]
        }
        df = pd.DataFrame(data)
        
        result = calculate_ratio_score(df)
        
        assert len(result) == 2
        # T1: 2/3, T2: 0/2
        t1_row = result[result["track_id"] == "T1"].iloc[0]
        t2_row = result[result["track_id"] == "T2"].iloc[0]
        
        assert np.isclose(t1_row["adolescent_exposure_score"], 2/3, atol=0.01)
        assert np.isclose(t2_row["adolescent_exposure_score"], 0.0, atol=0.01)

class TestFallback:
    def test_fallback_trigger(self):
        """Test that fallback is triggered when >50% missing."""
        data = {
            "track_id": ["T1", "T2", "T3", "T4"],
            "birth_year": [1990, None, None, 1995] # 2/4 missing = 50% -> not trigger?
        }
        # Need > 50%
        data = {
            "track_id": ["T1", "T2", "T3", "T4", "T5"],
            "birth_year": [1990, None, None, None, 1995] # 3/5 = 60%
        }
        df = pd.DataFrame(data)
        
        _, triggered = handle_fallback(df)
        assert triggered is True

    def test_no_fallback(self):
        """Test that fallback is NOT triggered when <50% missing."""
        data = {
            "track_id": ["T1", "T2", "T3"],
            "birth_year": [1990, None, 1995] # 1/3 = 33%
        }
        df = pd.DataFrame(data)
        
        _, triggered = handle_fallback(df)
        assert triggered is False
