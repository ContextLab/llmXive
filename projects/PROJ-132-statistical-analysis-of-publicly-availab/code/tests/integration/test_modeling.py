import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

def test_gamm_convergence():
    """Test GAMM fit on synthetic data."""
    # Create synthetic data
    np.random.seed(42)
    n = 100
    species = np.random.choice(["SpeciesA", "SpeciesB"], n)
    year = np.random.choice([2020, 2021], n)
    median_arrival = np.random.normal(15, 3, n)
    first_arrival = median_arrival + np.random.normal(0, 1, n)
    
    df = pd.DataFrame({
        "species": species,
        "year": year,
        "median_arrival": median_arrival,
        "first_arrival": first_arrival
    })
    
    # Import and run the fitting function
    import sys
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from src.models.gamm_fit import fit_species_year_gamm
    
    results = fit_species_year_gamm(df)
    
    # Verify results
    assert len(results) > 0
    assert all("species" in r for r in results)
    assert all("coefficient" in r for r in results)
    assert all("p_value" in r for r in results)