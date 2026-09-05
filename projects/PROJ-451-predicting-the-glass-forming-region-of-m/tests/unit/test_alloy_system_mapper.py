"""
Unit tests for features/alloy_system_mapper.py
"""

import pytest
import pandas as pd
from features.alloy_system_mapper import (
    parse_composition_to_dict,
    get_hill_sort_key,
    map_to_alloy_system,
    add_alloy_system_column
)

class TestParseComposition:
    def test_simple_binary(self):
        assert parse_composition_to_dict("Zr50Cu40Al10") == {'Zr': 50.0, 'Cu': 40.0, 'Al': 10.0}

    def test_water(self):
        assert parse_composition_to_dict("H2O") == {'H': 2.0, 'O': 1.0}

    def test_no_numbers(self):
        assert parse_composition_to_dict("CO2") == {'C': 1.0, 'O': 2.0}

    def test_empty_string(self):
        assert parse_composition_to_dict("") == {}

    def test_invalid_type(self):
        assert parse_composition_to_dict(123) == {}

    def test_complex_formula(self):
        # C6H12O6
        result = parse_composition_to_dict("C6H12O6")
        assert result == {'C': 6.0, 'H': 12.0, 'O': 6.0}

class TestHillSortKey:
    def test_c_first(self):
        assert get_hill_sort_key('C') < get_hill_sort_key('H')
        assert get_hill_sort_key('C') < get_hill_sort_key('Zr')

    def test_h_second(self):
        assert get_hill_sort_key('H') < get_hill_sort_key('Zr')
        assert get_hill_sort_key('H') > get_hill_sort_key('C')

    def test_alphabetical_others(self):
        assert get_hill_sort_key('Al') < get_hill_sort_key('Cu')
        assert get_hill_sort_key('Cu') < get_hill_sort_key('Zr')

class TestMapToAlloySystem:
    def test_zr_cu_al(self):
        # Zr is 50, Cu 40, Al 10 -> Base Zr. Secondaries: Cu, Al.
        # Sort secondaries: Al (Al), Cu (Cu). Hill order: Al < Cu.
        # Result: Zr-Al-Cu?
        # Wait, let's re-verify Hill order for secondary.
        # Secondary list: ['Cu', 'Al'].
        # Sort keys: Al -> (2, 0, 'Al'), Cu -> (2, 0, 'Cu').
        # Al < Cu. So sorted: ['Al', 'Cu'].
        # Output: "Zr-Al-Cu"
        result = map_to_alloy_system("Zr50Cu40Al10")
        assert result == "Zr-Al-Cu"

    def test_h2o(self):
        # H=2, O=1. Base=H. Secondary=O.
        # Output: "H-O"
        result = map_to_alloy_system("H2O")
        assert result == "H-O"

    def test_c6h12o6(self):
        # C=6, H=12, O=6. Base=H (12).
        # Secondaries: C, O.
        # Sort secondaries: C (0,0,'C'), O (2,0,'O'). C comes first.
        # Output: "H-C-O"
        result = map_to_alloy_system("C6H12O6")
        assert result == "H-C-O"

    def test_single_element(self):
        result = map_to_alloy_system("Fe100")
        assert result == "Fe"

    def test_tie_breaker(self):
        # Fe50Ni50. Base should be Fe (alphabetically before Ni in Hill order? No, both group 2. Alphabetical: Fe < Ni).
        # So Base = Fe. Secondary = Ni.
        # Output: "Fe-Ni"
        result = map_to_alloy_system("Fe50Ni50")
        assert result == "Fe-Ni"

    def test_empty_input(self):
        assert map_to_alloy_system("") == "Unknown"

class TestAddAlloySystemColumn:
    def test_basic_functionality(self):
        df = pd.DataFrame({'composition': ['Zr50Cu40Al10', 'H2O', 'Fe']})
        result = add_alloy_system_column(df, 'composition', 'alloy_system')
        assert 'alloy_system' in result.columns
        assert result.loc[0, 'alloy_system'] == "Zr-Al-Cu"
        assert result.loc[1, 'alloy_system'] == "H-O"
        assert result.loc[2, 'alloy_system'] == "Fe"

    def test_missing_column(self):
        df = pd.DataFrame({'other': ['a', 'b']})
        with pytest.raises(ValueError):
            add_alloy_system_column(df, 'composition', 'alloy_system')

    def test_dataframe_preservation(self):
        df = pd.DataFrame({'composition': ['Fe'], 'value': [1]})
        result = add_alloy_system_column(df, 'composition', 'alloy_system')
        assert 'value' in result.columns
        assert result.loc[0, 'value'] == 1
        assert len(result) == 1