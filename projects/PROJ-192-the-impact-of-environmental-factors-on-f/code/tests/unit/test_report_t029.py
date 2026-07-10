import os
import tempfile
import pandas as pd
import pytest
import numpy as np
from pathlib import Path
from src.pipelines.report import determine_top_drivers_and_ranking_stability

def test_determine_top_drivers_stability_pass():
    """
    Test case where top drivers are the same across biomes.
    Expected: SD = 0.0, Status = Pass.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create biome files with same top driver
        df1 = pd.DataFrame({'term': ['pH', 'Moisture'], 'R2': [0.5, 0.2]})
        df2 = pd.DataFrame({'term': ['pH', 'Moisture'], 'R2': [0.6, 0.3]})
        
        df1.to_csv(os.path.join(tmpdir, 'db_rda_biome_Forest.csv'), index=False)
        df2.to_csv(os.path.join(tmpdir, 'db_rda_biome_Grassland.csv'), index=False)
        
        output_path = os.path.join(tmpdir, 'biome_ranking_summary.csv')
        determine_top_drivers_and_ranking_stability(tmpdir, output_path)
        
        assert os.path.exists(output_path)
        result = pd.read_csv(output_path)
        
        assert 'status' in result.columns
        assert 'sd' in result.columns
        assert len(result) == 2
        assert result['status'].iloc[0] == 'Pass'
        assert result['sd'].iloc[0] == 0.0

def test_determine_top_drivers_stability_fail():
    """
    Test case where top drivers are very different.
    Expected: SD > 0.5, Status = Fail.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Biome 1: pH is top (Global Rank 0)
        # Biome 2: Moisture is top (Global Rank 1, assuming Moisture is 2nd best globally)
        # Biome 3: Nutrients is top (Global Rank 2)
        # Ranks: 0, 1, 2 -> Mean = 1, Variance = 2/3, SD = sqrt(0.66) ~ 0.81 > 0.5
        
        df1 = pd.DataFrame({'term': ['pH', 'Moisture', 'Nutrients'], 'R2': [0.5, 0.2, 0.1]})
        df2 = pd.DataFrame({'term': ['pH', 'Moisture', 'Nutrients'], 'R2': [0.1, 0.5, 0.2]})
        df3 = pd.DataFrame({'term': ['pH', 'Moisture', 'Nutrients'], 'R2': [0.1, 0.2, 0.5]})
        
        df1.to_csv(os.path.join(tmpdir, 'db_rda_biome_Forest.csv'), index=False)
        df2.to_csv(os.path.join(tmpdir, 'db_rda_biome_Grassland.csv'), index=False)
        df3.to_csv(os.path.join(tmpdir, 'db_rda_biome_Desert.csv'), index=False)
        
        output_path = os.path.join(tmpdir, 'biome_ranking_summary.csv')
        determine_top_drivers_and_ranking_stability(tmpdir, output_path)
        
        assert os.path.exists(output_path)
        result = pd.read_csv(output_path)
        
        assert result['status'].iloc[0] == 'Fail'
        assert result['sd'].iloc[0] > 0.5

def test_determine_top_drivers_empty():
    """Test with no input files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'biome_ranking_summary.csv')
        determine_top_drivers_and_ranking_stability(tmpdir, output_path)
        
        assert os.path.exists(output_path)
        result = pd.read_csv(output_path)
        assert len(result) == 0