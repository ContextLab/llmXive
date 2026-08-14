"""
Integration test for the ingestion pipeline with mock data.

This test verifies that the ingestion pipeline correctly filters data
to include only FCC self-diffusion entries and standardizes units.
"""
import pytest
import pandas as pd
import tempfile
import os
import sys
from pathlib import Path

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.ingestion import load_and_filter

def test_ingestion_pipeline():
    """
    Tests the ingestion pipeline with mock data containing mixed structures.
    
    Validates:
    1. Only FCC crystal structures are retained
    2. Only self-diffusion modes are retained
    3. Units are standardized to eV/atom
    4. Output contains correct number of rows
    """
    # Create mock data with mixed structures and diffusion modes
    mock_data = {
        "element": ["Cu", "Fe", "Al", "Ni", "W", "Mg"],
        "crystal_structure": ["FCC", "BCC", "FCC", "FCC", "BCC", "HCP"],
        "diffusion_mode": ["self", "self", "self", "interstitial", "self", "self"],
        "activation_energy_eV": [2.5, 3.0, 1.8, 2.2, 4.0, 1.5],
        "unit": ["eV/atom", "eV/atom", "eV/atom", "eV/atom", "eV/atom", "eV/atom"]
    }
    df = pd.DataFrame(mock_data)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    try:
        # Run ingestion pipeline
        filtered_df = load_and_filter(temp_path)
        
        # Assertions
        assert len(filtered_df) == 2, f"Expected 2 FCC self-diffusion rows, got {len(filtered_df)}"
        assert all(filtered_df['crystal_structure'] == 'FCC'), "Non-FCC rows should be filtered"
        assert all(filtered_df['diffusion_mode'] == 'self'), "Non-self diffusion modes should be filtered"
        
        # Verify units are standardized (should already be eV/atom in mock)
        assert all(filtered_df['unit'] == 'eV/atom'), "Units should be standardized to eV/atom"
        
        # Verify specific elements are retained (Cu and Al are FCC self)
        retained_elements = set(filtered_df['element'].tolist())
        assert retained_elements == {'Cu', 'Al'}, f"Expected Cu and Al, got {retained_elements}"
        
    finally:
        os.unlink(temp_path)

def test_ingestion_pipeline_empty_result():
    """
    Tests ingestion pipeline when no data matches criteria.
    """
    # Create mock data with no FCC self-diffusion
    mock_data = {
        "element": ["Fe", "W", "Mg"],
        "crystal_structure": ["BCC", "BCC", "HCP"],
        "diffusion_mode": ["self", "self", "self"],
        "activation_energy_eV": [3.0, 4.0, 1.5],
        "unit": ["eV/atom", "eV/atom", "eV/atom"]
    }
    df = pd.DataFrame(mock_data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    try:
        filtered_df = load_and_filter(temp_path)
        
        assert len(filtered_df) == 0, "Should return empty DataFrame when no matches"
        assert list(filtered_df.columns) == list(df.columns), "Column structure should be preserved"
        
    finally:
        os.unlink(temp_path)

def test_ingestion_pipeline_unit_conversion():
    """
    Tests that unit conversion from kJ/mol to eV/atom works correctly.
    """
    # 1 eV/atom ≈ 96.485 kJ/mol
    mock_data = {
        "element": ["Cu", "Al"],
        "crystal_structure": ["FCC", "FCC"],
        "diffusion_mode": ["self", "self"],
        "activation_energy_eV": [241.2125, 173.673],  # ~2.5 eV and ~1.8 eV in kJ/mol
        "unit": ["kJ/mol", "kJ/mol"]
    }
    df = pd.DataFrame(mock_data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    try:
        filtered_df = load_and_filter(temp_path)
        
        assert len(filtered_df) == 2, "Both rows should be retained"
        assert all(filtered_df['unit'] == 'eV/atom'), "Units should be converted to eV/atom"
        
        # Verify conversion: 241.2125 / 96.485 ≈ 2.5
        expected_cu = 241.2125 / 96.485
        actual_cu = filtered_df[filtered_df['element'] == 'Cu']['activation_energy_eV'].iloc[0]
        assert abs(actual_cu - expected_cu) < 0.01, f"Cu conversion failed: {actual_cu} vs {expected_cu}"
        
    finally:
        os.unlink(temp_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
