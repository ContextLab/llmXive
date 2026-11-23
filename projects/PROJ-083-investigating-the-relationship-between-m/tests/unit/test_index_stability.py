import pytest
from rdkit import Chem
from code.utils.symmetry import check_canonicalization_invariance, get_symmetry_classes
from code.descriptors import TopologicalDescriptorCalculator

class TestIndexStability:
    """
    Unit tests for index invariance under graph permutation (canonicalization).
    Implements T044, T045, T046 logic for preliminary verification.
    """

    def test_wiener_invariance_permutation(self):
        """
        Verify Wiener index remains constant under graph permutation (canonicalization).
        T044: Unit test for Wiener index invariance.
        """
        smiles = "c1ccccc1"
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, "Failed to parse benzene"

        result = check_canonicalization_invariance(smiles)
        assert result is True, f"Wienner invariance check failed for {smiles}"

    def test_balaban_invariance_permutation(self):
        """
        Verify Balaban index remains constant under graph permutation.
        T045: Unit test for Balaban index invariance.
        
        Logic:
        1. Parse the original SMILES.
        2. Calculate the Balaban index for the original molecule.
        3. Canonicalize the SMILES string (which permutes atom indices).
        4. Re-parse the canonical SMILES.
        5. Calculate the Balaban index for the canonicalized molecule.
        6. Assert that the two indices are equal (within floating point tolerance).
        """
        test_cases = [
            ("Benzene", "c1ccccc1"),
            ("Toluene", "Cc1ccccc1"),
            ("Nitrobenzene", "c1ccccc1[N+](=O)[O-]"),
            ("Naphthalene", "c1ccc2ccccc2c1"),
        ]

        for name, smiles in test_cases:
            mol = Chem.MolFromSmiles(smiles)
            assert mol is not None, f"Failed to parse {name}: {smiles}"

            # Calculate original Balaban index
            # Using RDKit's CalcBalabanIndex if available, otherwise fallback to our calculator
            try:
                from rdkit.Chem import rdMolDescriptors
                balaban_orig = rdMolDescriptors.CalcBalabanIndex(mol)
            except AttributeError:
                # Fallback to project implementation if RDKit version lacks it
                calc = TopologicalDescriptorCalculator(mol)
                balaban_orig = calc.calculate_balaban_index()

            # Canonicalize SMILES
            # isomericSmiles=False ensures we only test topological permutation, not stereochemistry
            canonical_smiles = Chem.MolToSmiles(mol, isomericSmiles=False, canonical=True)
            
            mol_canon = Chem.MolFromSmiles(canonical_smiles)
            assert mol_canon is not None, f"Failed to re-parse canonicalized {name}"

            # Calculate canonical Balaban index
            try:
                from rdkit.Chem import rdMolDescriptors
                balaban_canon = rdMolDescriptors.CalcBalabanIndex(mol_canon)
            except AttributeError:
                calc_canon = TopologicalDescriptorCalculator(mol_canon)
                balaban_canon = calc_canon.calculate_balaban_index()

            # Assert equality with tolerance for floating point arithmetic
            # Balaban indices are typically small floats; 1e-6 tolerance is safe
            assert abs(balaban_orig - balaban_canon) < 1e-6, (
                f"Balaban index invariance failed for {name} ({smiles}). "
                f"Original: {balaban_orig}, Canonical: {balaban_canon}"
            )

    def test_zagreb_invariance_permutation(self):
        """
        Verify Zagreb index remains constant under graph permutation.
        T046: Unit test for Zagreb index invariance.
        
        Logic:
        1. Parse the original SMILES.
        2. Calculate the First Zagreb index (sum of squared degrees) for the original molecule.
        3. Canonicalize the SMILES string (which permutes atom indices).
        4. Re-parse the canonical SMILES.
        5. Calculate the First Zagreb index for the canonicalized molecule.
        6. Assert that the two indices are equal.
        
        The Zagreb index is a topological invariant based on vertex degrees.
        Since graph canonicalization preserves the graph structure (adjacency),
        the degree sequence remains identical, and thus the sum of squared degrees
        must be identical.
        """
        test_cases = [
            ("Benzene", "c1ccccc1"),
            ("Toluene", "Cc1ccccc1"),
            ("Nitrobenzene", "c1ccccc1[N+](=O)[O-]"),
            ("Naphthalene", "c1ccc2ccccc2c1"),
            ("Ethanol", "CCO"),
        ]

        for name, smiles in test_cases:
            mol = Chem.MolFromSmiles(smiles)
            assert mol is not None, f"Failed to parse {name}: {smiles}"

            # Calculate original Zagreb index (First Zagreb Index M1)
            # M1 = sum(degree(v)^2 for v in vertices)
            try:
                from rdkit.Chem import rdMolDescriptors
                # RDKit does not have a direct CalcZagrebIndex in all versions,
                # so we compute it manually to ensure consistency with our descriptor module
                mol_no_h = Chem.RemoveHs(mol)
                adj_matrix = Chem.GetAdjacencyMatrix(mol_no_h)
                degrees = np.sum(adj_matrix, axis=1)
                zagreb_orig = np.sum(degrees ** 2)
            except Exception:
                # Fallback to project implementation if RDKit utilities fail
                calc = TopologicalDescriptorCalculator(mol)
                zagreb_orig = calc.calculate_zagreb_index()

            # Canonicalize SMILES
            canonical_smiles = Chem.MolToSmiles(mol, isomericSmiles=False, canonical=True)
            
            mol_canon = Chem.MolFromSmiles(canonical_smiles)
            assert mol_canon is not None, f"Failed to re-parse canonicalized {name}"

            # Calculate canonical Zagreb index
            try:
                from rdkit.Chem import rdMolDescriptors
                mol_no_h_canon = Chem.RemoveHs(mol_canon)
                adj_matrix_canon = Chem.GetAdjacencyMatrix(mol_no_h_canon)
                degrees_canon = np.sum(adj_matrix_canon, axis=1)
                zagreb_canon = np.sum(degrees_canon ** 2)
            except Exception:
                calc_canon = TopologicalDescriptorCalculator(mol_canon)
                zagreb_canon = calc_canon.calculate_zagreb_index()

            # Assert equality. Zagreb indices are integers for simple graphs,
            # so exact equality is expected, but we use a small tolerance for float safety.
            assert abs(zagreb_orig - zagreb_canon) < 1e-9, (
                f"Zagreb index invariance failed for {name} ({smiles}). "
                f"Original: {zagreb_orig}, Canonical: {zagreb_canon}"
            )

    def test_invariance_failure_on_malformed(self):
        """
        Ensure the function handles invalid SMILES gracefully.
        """
        with pytest.raises(ValueError):
            check_canonicalization_invariance("invalid_smiles_string")

    def test_symmetry_classes_consistency(self):
        """
        Verify that symmetry classes are consistent for a known symmetric molecule.
        """
        smiles = "c1ccccc1"
        mol = Chem.MolFromSmiles(smiles)
        classes = get_symmetry_classes(mol)
        
        # Benzene has 6 atoms, all equivalent -> 1 symmetry class
        assert len(set(classes)) == 1, "Benzene should have 1 symmetry class"

    def test_symmetry_classes_asymmetric(self):
        """
        Verify symmetry classes for an asymmetric molecule.
        """
        smiles = "CC(O)C(=O)O" # Lactic acid (chiral, asymmetric carbons)
        mol = Chem.MolFromSmiles(smiles)
        classes = get_symmetry_classes(mol)
        
        # There should be more than 1 class
        assert len(set(classes)) > 1, "Lactic acid should have multiple symmetry classes"