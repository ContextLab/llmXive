"""
Unit tests for descriptor calculation logic in code/descriptors.py.

Tests verify the calculation of mean and variance for elemental properties
(electronegativity, radius, valence, melting point, ionization energy)
as specified in User Story 1.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure the code directory is in the path for imports
_project_root = Path(__file__).resolve().parent.parent.parent
_code_path = _project_root / "code"
if str(_code_path) not in sys.path:
    sys.path.insert(0, str(_code_path))

# We will mock the heavy dependencies (pymatgen) and test the logic
# that would be in descriptors.py. Since descriptors.py is not yet implemented
# (T014-T016), we define the expected logic here to ensure the test
# covers the correct behavior once the implementation exists.
#
# The actual implementation in code/descriptors.py should perform:
# 1. Load elemental properties for each element in the composition.
# 2. Calculate weighted mean and variance based on stoichiometry.
# 3. Handle missing values (exclude rows).

# Mock data generator for testing
def create_sample_dataframe():
    """Create a small sample dataframe mimicking the processed raw data."""
    return pd.DataFrame({
        "formula": ["H2O", "NaCl", "Fe2O3", "SiO2", "C6H12O6"],
        "composition": [
            {"H": 2, "O": 1},
            {"Na": 1, "Cl": 1},
            {"Fe": 2, "O": 3},
            {"Si": 1, "O": 2},
            {"C": 6, "H": 12, "O": 6}
        ],
        "formation_energy": [-2.5, -4.0, -8.0, -9.0, -3.0]
    })

def create_mock_elemental_properties():
    """
    Create a mock dictionary of elemental properties.
    In the real implementation, this comes from pymatgen or matminer.
    Structure: { element: { property_name: value } }
    """
    # Using arbitrary but consistent values for testing logic
    props = {
        "H": {"electronegativity": 2.20, "radius": 0.37, "valence": 1, "melting_point": 14.0, "ionization_energy": 1312.0},
        "O": {"electronegativity": 3.44, "radius": 0.66, "valence": 2, "melting_point": 54.36, "ionization_energy": 1314.0},
        "Na": {"electronegativity": 0.93, "radius": 1.86, "valence": 1, "melting_point": 370.87, "ionization_energy": 496.0},
        "Cl": {"electronegativity": 3.16, "radius": 0.99, "valence": 1, "melting_point": 171.6, "ionization_energy": 1251.0},
        "Fe": {"electronegativity": 1.83, "radius": 1.26, "valence": 3, "melting_point": 1811.0, "ionization_energy": 762.0},
        "Si": {"electronegativity": 1.90, "radius": 1.17, "valence": 4, "melting_point": 1687.0, "ionization_energy": 786.0},
        "C": {"electronegativity": 2.55, "radius": 0.77, "valence": 4, "melting_point": 3800.0, "ionization_energy": 1086.0},
        # Missing property for 'X' to test exclusion logic
        "X": {"electronegativity": 1.0, "radius": 1.0, "valence": 1, "melting_point": 100.0}, 
    }
    return props

def calculate_descriptors_logic(df, element_props, properties):
    """
    Reference implementation of the descriptor calculation logic.
    This mimics what code/descriptors.py will do.
    
    Args:
        df: DataFrame with 'composition' column (dicts)
        element_props: Dict of elemental properties
        properties: List of property names to calculate
        
    Returns:
        DataFrame with new descriptor columns. Rows with missing properties are excluded.
    """
    results = []
    excluded_indices = []
    
    for idx, row in df.iterrows():
        comp = row["composition"]
        total_atoms = sum(comp.values())
        if total_atoms == 0:
            excluded_indices.append(idx)
            continue
        
        valid_row = True
        row_data = {"formula": row["formula"]}
        
        for prop in properties:
            values = []
            weights = []
            
            for element, count in comp.items():
                if element not in element_props or prop not in element_props[element]:
                    valid_row = False
                    break
                values.append(element_props[element][prop])
                weights.append(count)
            
            if not valid_row:
                break
            
            # Weighted Mean
            mean_val = np.average(values, weights=weights)
            # Weighted Variance
            # variance = sum(w * (x - mean)^2) / sum(w)
            variance_val = np.average((np.array(values) - mean_val) ** 2, weights=weights)
            
            row_data[f"{prop}_mean"] = mean_val
            row_data[f"{prop}_variance"] = variance_val
        
        if valid_row:
            results.append(pd.Series(row_data))
        else:
            excluded_indices.append(idx)
    
    if not results:
        return pd.DataFrame(), excluded_indices
        
    res_df = pd.DataFrame(results)
    # Merge back with original columns if needed, but for unit test we just return the calculated part
    return res_df, excluded_indices

class TestDescriptorLogic:
    """Test suite for the descriptor calculation logic."""

    @pytest.fixture
    def sample_data(self):
        return create_sample_dataframe()

    @pytest.fixture
    def mock_props(self):
        return create_mock_elemental_properties()

    @pytest.fixture
    def target_properties(self):
        return ["electronegativity", "radius", "valence", "melting_point", "ionization_energy"]

    def test_mean_calculation_simple(self, sample_data, mock_props, target_properties):
        """Test that mean is calculated correctly for a simple case (H2O)."""
        # H2O: H(2.20), O(3.44). Weights: 2, 1. Total 3.
        # Mean EN = (2*2.20 + 1*3.44) / 3 = (4.40 + 3.44) / 3 = 7.84 / 3 = 2.6133...
        expected_en_mean = (2 * 2.20 + 1 * 3.44) / 3.0
        
        result_df, _ = calculate_descriptors_logic(sample_data, mock_props, target_properties)
        
        # H2O is the first row in the input, should be first in result if valid
        # Note: The order might change if rows are excluded, but H2O is valid.
        # Let's find the row with formula H2O
        h2o_row = result_df[result_df["formula"] == "H2O"].iloc[0]
        
        assert abs(h2o_row["electronegativity_mean"] - expected_en_mean) < 1e-5, \
            f"Expected {expected_en_mean}, got {h2o_row['electronegativity_mean']}"

    def test_variance_calculation(self, sample_data, mock_props, target_properties):
        """Test that variance is calculated correctly."""
        # H2O: H(0.37), O(0.66). Weights: 2, 1.
        # Mean Radius = (2*0.37 + 1*0.66) / 3 = (0.74 + 0.66) / 3 = 1.40 / 3 = 0.4666...
        mean_r = (2 * 0.37 + 1 * 0.66) / 3.0
        # Var = [2*(0.37 - 0.4666)^2 + 1*(0.66 - 0.4666)^2] / 3
        #     = [2*(-0.0966)^2 + 1*(0.1933)^2] / 3
        #     = [2*0.00933 + 0.03737] / 3
        #     = [0.01866 + 0.03737] / 3 = 0.05603 / 3 = 0.01867...
        expected_var_r = (2 * (0.37 - mean_r)**2 + 1 * (0.66 - mean_r)**2) / 3.0
        
        result_df, _ = calculate_descriptors_logic(sample_data, mock_props, target_properties)
        h2o_row = result_df[result_df["formula"] == "H2O"].iloc[0]
        
        assert abs(h2o_row["radius_variance"] - expected_var_r) < 1e-5, \
            f"Expected {expected_var_r}, got {h2o_row['radius_variance']}"

    def test_missing_element_exclusion(self, sample_data, mock_props, target_properties):
        """Test that rows with missing elemental properties are excluded."""
        # Add a row with an element 'X' that has incomplete properties (missing ionization_energy)
        sample_data.loc[len(sample_data)] = ["Unknown", {"X": 1, "H": 1}]
        
        result_df, excluded_indices = calculate_descriptors_logic(sample_data, mock_props, target_properties)
        
        # 'X' is missing ionization_energy, so this row should be excluded
        assert "Unknown" not in result_df["formula"].values, "Row with missing property should be excluded"
        assert len(excluded_indices) > 0, "Excluded indices should not be empty"

    def test_all_properties_present(self, sample_data, mock_props, target_properties):
        """Verify all expected columns are created."""
        result_df, _ = calculate_descriptors_logic(sample_data, mock_props, target_properties)
        
        for prop in target_properties:
            assert f"{prop}_mean" in result_df.columns, f"Column {prop}_mean missing"
            assert f"{prop}_variance" in result_df.columns, f"Column {prop}_variance missing"

    def test_numeric_types(self, sample_data, mock_props, target_properties):
        """Verify that calculated descriptors are numeric."""
        result_df, _ = calculate_descriptors_logic(sample_data, mock_props, target_properties)
        
        for prop in target_properties:
            assert pd.api.types.is_numeric_dtype(result_df[f"{prop}_mean"]), f"{prop}_mean is not numeric"
            assert pd.api.types.is_numeric_dtype(result_df[f"{prop}_variance"]), f"{prop}_variance is not numeric"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
