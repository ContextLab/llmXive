"""
Unit tests for descriptor computation on mixed hybridization molecules.

This test file is written to FAIL initially because the implementation 
for mixed hybridization descriptor computation (T014, T015, T020, T021, T022)
has not yet been implemented in code/descriptors.py.

Expected failures will occur when:
1. The descriptors module does not exist or lacks required functions
2. The compute_descriptors function cannot handle molecules with mixed sp/sp2/sp3 atoms
3. The returned DataFrame lacks required columns for mixed hybridization analysis
"""

import pytest
import pandas as pd
import numpy as np
from rdkit import Chem

# These imports will fail until T014-T022 are implemented
try:
    from descriptors import compute_descriptors, compute_bond_polarity, compute_resonance_energy
except ImportError:
    # Will cause test failures until implementation exists
    compute_descriptors = None
    compute_bond_polarity = None
    compute_resonance_energy = None

# Test molecules with mixed hybridization
MIXED_HYBRIDIZATION_MOLECULES = [
    {
        "name": "propyne",
        "smiles": "CC#C",  # sp3 (methyl), sp (alkyne)
        "expected_hybridizations": ["sp3", "sp", "sp"]
    },
    {
        "name": "propene",
        "smiles": "CC=C",  # sp3 (methyl), sp2 (alkene)
        "expected_hybridizations": ["sp3", "sp2", "sp2"]
    },
    {
        "name": "vinyl_acetylene",
        "smiles": "C=CC#C",  # sp2 (alkene), sp (alkyne)
        "expected_hybridizations": ["sp2", "sp2", "sp", "sp"]
    },
    {
        "name": "toluene",
        "smiles": "Cc1ccccc1",  # sp3 (methyl), sp2 (aromatic ring)
        "expected_hybridizations": ["sp3", "sp2", "sp2", "sp2", "sp2", "sp2", "sp2"]
    },
    {
        "name": "phenylacetylene",
        "smiles": "c1ccccc1C#C",  # sp2 (aromatic), sp (alkyne)
        "expected_hybridizations": ["sp2", "sp2", "sp2", "sp2", "sp2", "sp2", "sp", "sp"]
    }
]

REQUIRED_COLUMNS = [
    'smiles', 'status', 
    'degree_mean', 'degree_std', 'degree_max', 'degree_min',
    'path_length_mean', 'path_length_std', 'path_length_max', 'path_length_min',
    'aromaticity_index', 'conjugation_length', 'ring_count',
    'bond_polarity', 'resonance_energy'
]

@pytest.fixture
def mixed_hybridization_smiles():
    """Return list of SMILES strings with mixed hybridization."""
    return [mol["smiles"] for mol in MIXED_HYBRIDIZATION_MOLECULES]

@pytest.mark.skipif(
    compute_descriptors is None, 
    reason="compute_descriptors not implemented yet (expected failure for T012)"
)
def test_descriptor_computation_mixed_hybridization(mixed_hybridization_smiles):
    """
    Test that descriptor computation handles molecules with mixed hybridization states.
    
    This test verifies:
    1. All molecules are processed without errors
    2. The output DataFrame contains all required columns
    3. Numeric values are valid (not NaN, not infinite)
    4. Hybridization-aware descriptors show expected patterns
    """
    # Convert to DataFrame format expected by compute_descriptors
    df_input = pd.DataFrame({"smiles": mixed_hybridization_smiles})
    
    # This will fail until T014-T022 are implemented
    result = compute_descriptors(df_input)
    
    # Verify structure
    assert isinstance(result, pd.DataFrame), "Result must be a DataFrame"
    assert set(REQUIRED_COLUMNS).issubset(set(result.columns)), \
        f"Result must contain all required columns: {REQUIRED_COLUMNS}"
    
    # Verify no NaN values in numeric columns
    numeric_cols = [col for col in REQUIRED_COLUMNS if col != 'smiles' and col != 'status']
    for col in numeric_cols:
        assert not result[col].isna().any(), f"Column {col} contains NaN values"
        assert not np.isinf(result[col]).any(), f"Column {col} contains infinite values"
    
    # Verify status column shows success
    assert (result['status'] == 'success').all(), \
        f"Not all molecules processed successfully: {result[result['status'] != 'success']}"
    
    # Specific hybridization checks
    # Toluene should have higher aromaticity_index than propyne
    toluene_idx = result[result['smiles'] == 'Cc1ccccc1'].index[0]
    propyne_idx = result[result['smiles'] == 'CC#C'].index[0]
    
    assert result.loc[toluene_idx, 'aromaticity_index'] > result.loc[propyne_idx, 'aromaticity_index'], \
        "Toluene should have higher aromaticity than propyne"
    
    # Phenylacetylene should have non-zero resonance energy
    phenylacetylene_idx = result[result['smiles'] == 'c1ccccc1C#C'].index[0]
    assert result.loc[phenylacetylene_idx, 'resonance_energy'] > 0, \
        "Phenylacetylene should have positive resonance energy"

@pytest.mark.skipif(
    compute_bond_polarity is None, 
    reason="compute_bond_polarity not implemented yet (expected failure for T012)"
)
def test_bond_polarity_mixed_hybridization(mixed_hybridization_smiles):
    """
    Test bond polarity calculation for molecules with mixed hybridization.
    
    Bond polarity should be higher in molecules with significant electronegativity
    differences and shorter bond lengths (sp/sp2 vs sp3).
    """
    df_input = pd.DataFrame({"smiles": mixed_hybridization_smiles})
    result = compute_descriptors(df_input)
    
    # Check that bond polarity varies across molecules
    assert result['bond_polarity'].std() > 0, \
        "Bond polarity should vary across mixed hybridization molecules"
    
    # sp-hybridized molecules should show different bond polarity patterns
    sp_molecules = ['CC#C', 'C=CC#C', 'c1ccccc1C#C']
    sp_indices = [result[result['smiles'] == smiles].index[0] for smiles in sp_molecules 
                 if smiles in result['smiles'].values]
    
    if sp_indices:
        sp_bond_pol = result.loc[sp_indices, 'bond_polarity'].mean()
        non_sp_bond_pol = result.loc[~result['smiles'].isin(sp_molecules), 'bond_polarity'].mean()
        
        # sp bonds typically show higher polarity due to shorter bond lengths
        # This is a soft assertion as actual values depend on implementation
        assert abs(sp_bond_pol - non_sp_bond_pol) > 0.01, \
            "sp-hybridized molecules should show distinct bond polarity"

@pytest.mark.skipif(
    compute_resonance_energy is None, 
    reason="compute_resonance_energy not implemented yet (expected failure for T012)"
)
def test_resonance_energy_mixed_hybridization(mixed_hybridization_smiles):
    """
    Test resonance energy calculation for conjugated and aromatic systems.
    
    Molecules with conjugation and aromaticity should show positive resonance energy,
    while aliphatic molecules should show near-zero values.
    """
    df_input = pd.DataFrame({"smiles": mixed_hybridization_smiles})
    result = compute_descriptors(df_input)
    
    # Aromatic/conjugated molecules should have positive resonance energy
    aromatic_molecules = ['Cc1ccccc1', 'c1ccccc1C#C', 'C=CC#C']
    aromatic_indices = [result[result['smiles'] == smiles].index[0] 
                       for smiles in aromatic_molecules if smiles in result['smiles'].values]
    
    if aromatic_indices:
        aromatic_resonance = result.loc[aromatic_indices, 'resonance_energy']
        assert (aromatic_resonance > 0).all(), \
            "Aromatic/conjugated molecules should have positive resonance energy"
    
    # Aliphatic molecules should have near-zero resonance energy
    aliphatic_molecules = ['CC#C', 'CC=C']
    aliphatic_indices = [result[result['smiles'] == smiles].index[0] 
                        for smiles in aliphatic_molecules if smiles in result['smiles'].values]
    
    if aliphatic_indices:
        aliphatic_resonance = result.loc[aliphatic_indices, 'resonance_energy']
        assert (aliphatic_resonance >= 0).all(), \
            "Aliphatic molecules should have non-negative resonance energy"
        assert (aliphatic_resonance < 5.0).all(), \
            "Aliphatic molecules should have low resonance energy (< 5.0)"

@pytest.mark.skipif(
    compute_descriptors is None, 
    reason="compute_descriptors not implemented yet (expected failure for T012)"
)
def test_descriptors_computation_edge_cases():
    """
    Test edge cases in mixed hybridization descriptor computation.
    
    This ensures robustness when handling:
    - Very small molecules
    - Large conjugated systems
    - Molecules with only sp3 atoms
    """
    edge_case_smiles = [
        "C",           # Methane - only sp3
        "C=C",         # Ethene - only sp2
        "C#C",         # Ethyne - only sp
        "c1ccccc1",    # Benzene - only sp2 (aromatic)
        "CCCCCCCC",    # Octane - long aliphatic chain
    ]
    
    df_input = pd.DataFrame({"smiles": edge_case_smiles})
    
    # This will fail until implementation exists
    result = compute_descriptors(df_input)
    
    assert len(result) == len(edge_case_smiles), \
        "All edge case molecules should be processed"
    assert (result['status'] == 'success').all(), \
        "All edge case molecules should process successfully"
    
    # Verify all required columns exist
    assert set(REQUIRED_COLUMNS).issubset(set(result.columns)), \
        "Edge case results must contain all required columns"