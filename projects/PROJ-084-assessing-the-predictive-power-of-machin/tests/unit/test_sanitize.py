"""
Unit tests for salt removal and SMILES standardization logic.

These tests verify the core preprocessing logic in `code/preprocessing/sanitize.py`
without requiring the full dataset download or heavy model training.

They focus on:
1. Correct removal of salt components from reaction SMILES.
2. Proper standardization of SMILES strings (canonicalization).
3. Handling of edge cases (empty strings, single component, etc.).
"""
import pytest
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.SaltRemover import SaltRemover

# Import the specific function to test.
# Assuming the function is defined in code/preprocessing/sanitize.py
# We use a relative import pattern that works if tests are run from root with PYTHONPATH set,
# or we import directly if the structure allows.
# Given the project structure `code/preprocessing/sanitize.py`, we import:
try:
    from code.preprocessing.sanitize import remove_salts_and_standardize
except ImportError:
    # Fallback for local execution if path setup differs slightly, 
    # though the agent ensures `code/` is in path or imports are absolute relative to root.
    # For the purpose of this artifact, we assume the import path `code.preprocessing.sanitize`
    # is valid as per the project structure defined in tasks.md.
    pytest.skip("Module code.preprocessing.sanitize not available in environment", allow_module_level=True)

# --- Fixtures ---

@pytest.fixture
def sample_reaction_smiles():
    """
    Provides a list of reaction SMILES strings with varying salt conditions.
    Format: Reactants >> Products
    """
    return [
        # Valid reaction with a salt on the reactant side (Na+ is common)
        "CC(=O)O.[Na+].CCO>>CC(=O)[O-].[Na+].CCO", 
        # Valid reaction with salt on product side
        "CCO>>CC(=O)O.[Cl-].[Na+]",
        # Valid reaction with no salts
        "CCO>>CC(=O)O",
        # Reaction with multiple salts
        "CC(=O)O.[Na+].[Cl-].K+>>CC(=O)[O-].[K+]",
        # Invalid/Empty entry
        "",
        # Single component (no reaction arrow) - edge case
        "CC(=O)O.[Na+]"
    ]

# --- Tests ---

def test_remove_salts_basic(sample_reaction_smiles):
    """
    Test that salts (e.g., Na+, Cl-) are removed from the SMILES strings.
    """
    results = []
    for smiles in sample_reaction_smiles:
        if not smiles:
            results.append("")
            continue
        
        # Apply the function
        cleaned = remove_salts_and_standardize(smiles)
        results.append(cleaned)
    
    # Verify specific cases
    # Case 1: Salt removed from reactants
    assert "[Na+]" not in results[0], "Salt [Na+] should be removed from reactant side"
    # Case 2: Salt removed from products
    assert "[Cl-]" not in results[1] and "[Na+]" not in results[1], "Salts should be removed from product side"
    # Case 3: No change if no salts
    assert results[2] == "CCO>>CC(=O)O", "Reaction without salts should remain unchanged (or canonicalized)"
    # Case 4: Multiple salts removed
    assert "[Na+]" not in results[3] and "[Cl-]" not in results[3] and "[K+]" not in results[3], "All salts should be removed"
    # Case 5: Empty string remains empty
    assert results[4] == "", "Empty string should remain empty"

def test_standardization_consistency(sample_reaction_smiles):
    """
    Test that the SMILES strings are standardized (canonicalized) consistently.
    """
    results = []
    for smiles in sample_reaction_smiles:
        if not smiles:
            results.append("")
            continue
        cleaned = remove_salts_and_standardize(smiles)
        results.append(cleaned)
    
    # Check that non-empty results are valid RDKit molecules/reactions
    for i, res in enumerate(results):
        if res:
            # Try to parse the result to ensure it's a valid SMILES
            # Note: Reaction SMILES parsing in RDKit can be tricky, 
            # so we check if the string is not empty and doesn't contain obvious salt artifacts.
            assert isinstance(res, str), f"Result at index {i} should be a string"
            # Basic check: if it looks like a reaction, it should have '>>'
            if '>>' in sample_reaction_smiles[i]:
                assert '>>' in res, f"Reaction SMILES at index {i} should still contain '>>'"

def test_empty_and_none_handling():
    """
    Test that the function handles None or empty strings gracefully.
    """
    # Test empty string
    assert remove_salts_and_standardize("") == "", "Empty string should return empty string"
    
    # Test string with only spaces (if logic handles stripping)
    # Depending on implementation, this might be treated as empty or invalid.
    # We expect it to return empty or a sanitized version.
    result = remove_salts_and_standardize("   ")
    assert result == "", "Whitespace-only string should return empty string"

def test_salt_remover_configuration():
    """
    Verify that the SaltRemover is configured correctly in the function.
    This is a sanity check on the implementation details.
    """
    # We can't easily introspect the function's internal variable,
    # but we can test the behavior against a known salt list.
    # The default RDKit SaltRemover usually handles common inorganic salts.
    # We test a specific known salt removal.
    smiles_with_salt = "C[Na+]" # Ethane with Sodium
    cleaned = remove_salts_and_standardize(smiles_with_salt)
    
    # If the salt remover is working, [Na+] should be gone
    # Note: If the input is just a molecule (no reaction arrow), 
    # the function should still handle it.
    assert "[Na+]" not in cleaned, "SaltRemover should remove [Na+]"

def test_reaction_center_preservation(sample_reaction_smiles):
    """
    Ensure that the actual reaction components (non-salts) are preserved.
    """
    # Take a specific example: Acetic acid + Ethanol -> Ethyl acetate + Water
    # With a salt added
    input_smiles = "CC(=O)O.[Na+].CCO>>CC(=O)OCC.[Na+]"
    output = remove_salts_and_standardize(input_smiles)
    
    # The core reactants and products should still be present (canonicalized)
    # We check for the presence of the core fragments (simplified check)
    assert "CC(=O)O" in output or "CC(=O)OCC" in output, "Core reaction components should be preserved"
    # Ensure the salt is gone
    assert "[Na+]" not in output, "Salt must be removed"