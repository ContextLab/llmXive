import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from src.pipelines.report import apply_fdr_correction, generate_permanova_summary, generate_db_rda_biome_results

def test_apply_fdr_correction():
    """Test that FDR correction is applied correctly."""
    df = pd.DataFrame({
        "term": ["pH", "Nutrients", "Moisture"],
        "R2": [0.1, 0.2, 0.3],
        "p-value": [0.01, 0.04, 0.05]
    })
    
    result = apply_fdr_correction(df, "p-value")
    
    assert "p-value_adj" in result.columns
    assert len(result) == 3
    # Check that adjusted values are different from raw (unless all 1 or 0)
    assert not result["p-value_adj"].equals(result["p-value"])

def test_generate_db_rda_biome_results():
    """Test generation of biome-specific db-RDA CSV."""
    df = pd.DataFrame({
        "term": ["pH", "Organic_Carbon"],
        "R2": [0.15, 0.10],
        "p-value": [0.001, 0.02]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = generate_db_rda_biome_results(df, "Temperate_Forest", tmpdir)
        
        assert output_path != ""
        assert os.path.exists(output_path)
        assert "db_rda_biome_Temperate_Forest.csv" in output_path
        
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 2
        assert "R2" in loaded_df.columns

def test_generate_db_rda_biome_results_empty():
    """Test behavior with empty dataframe."""
    df = pd.DataFrame()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = generate_db_rda_biome_results(df, "Desert", tmpdir)
        
        assert output_path == ""