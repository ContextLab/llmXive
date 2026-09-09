import pytest
import pandas as pd
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.ingestion import fetch_dataset_data, load_fallback_data, filter_electrolytes, deduplicate_by_id_potential, run_ingestion_pipeline
from config import get_project_root, get_raw_dir

class TestIngestionPipeline:
    
    def test_load_fallback_data(self):
        """Test loading the mock fallback CSV."""
        root = get_project_root()
        if not root:
            pytest.skip("Project root not configured")
            
        fallback_path = root / "data" / "raw" / "mock_electrolytes.csv"
        
        # Ensure fallback file exists
        if not fallback_path.exists():
            pytest.fail(f"Fallback file not found at {fallback_path}. Create it to run this test.")
        
        df = load_fallback_data()
        
        assert df is not None
        assert not df.empty
        assert 'molecule_id' in df.columns
        assert 'potential_v' in df.columns
        assert 'smiles' in df.columns
        assert 'reactant_energy' in df.columns
        assert 'product_energy' in df.columns

    def test_filter_electrolytes(self):
        """Test filtering logic for specific molecules."""
        df = pd.DataFrame({
            'molecule_id': ['EC_0V', 'DMC_0V', 'LiPF6_0V', 'H2O_0V'],
            'potential_v': [0, 0, 0, 0],
            'smiles': ['C1OC(=O)O1', 'COC(=O)OC', '[Li+].[F-]P(=O)([F-])[F-]', 'O'],
            'reactant_energy': [-1, -2, -3, -4],
            'product_energy': [-1.1, -2.1, -3.1, -4.1]
        })
        
        filtered = filter_electrolytes(df, target_ids=['EC_0V', 'DMC_0V'])
        
        assert len(filtered) == 2
        assert 'H2O_0V' not in filtered['molecule_id'].values

    def test_deduplicate(self):
        """Test deduplication by molecule_id and potential."""
        df = pd.DataFrame({
            'molecule_id': ['EC_0V', 'EC_0V', 'EC_2V', 'EC_2V'],
            'potential_v': [0, 0, 2, 2],
            'smiles': ['C1OC(=O)O1'] * 4,
            'reactant_energy': [1, 1, 2, 2],
            'product_energy': [1.1, 1.2, 2.1, 2.2]
        })
        
        deduped = deduplicate_by_id_potential(df)
        
        assert len(deduped) == 2
        # Check that duplicates are removed (first occurrence kept by default pandas drop_duplicates)
        assert len(deduped[deduped['molecule_id'] == 'EC_0V']) == 1

    def test_run_ingestion_pipeline_fallback(self):
        """Test the full pipeline using fallback data."""
        root = get_project_root()
        if not root:
            pytest.skip("Project root not configured")
            
        fallback_path = root / "data" / "raw" / "mock_electrolytes.csv"
        if not fallback_path.exists():
            pytest.fail(f"Fallback file missing: {fallback_path}")
        
        # Run pipeline
        df = run_ingestion_pipeline(use_fallback=True)
        
        assert df is not None
        assert not df.empty
        assert 'molecule_id' in df.columns
        assert 'potential_v' in df.columns
        assert 'smiles' in df.columns
        assert 'reactant_energy' in df.columns
        assert 'product_energy' in df.columns
        assert 'decomp_energy' in df.columns # Assuming target calc is part of pipeline or expected output