"""
Unit tests for Materials Project data ingestion (T010b).

Tests verify:
1. Configuration loading works correctly
2. Data processing functions handle edge cases
3. Output format is correct
"""

import pytest
import pandas as pd
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.ingest_mp import (
    fetch_materials_project_compositions,
    fetch_materials_project_elements,
    process_mp_data
)
from utils.config import get_materials_project_api_key


class TestFetchMaterialsProjectCompositions:
    """Tests for the fetch_materials_project_compositions function."""
    
    def test_fetch_with_valid_api_key(self):
        """Test fetching with a valid API key."""
        with patch('scripts.ingest_mp.requests.get') as mock_get:
            # Mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [
                    {
                        "material_id": "mp-12345",
                        "formula_pretty": "Fe2O3",
                        "formula_anonymous": "A2B3",
                        "nelements": 2,
                        "nsites": 5,
                        "energy_per_atom": -5.2,
                        "formation_energy_per_atom": -2.1,
                        "band_gap": 0.0,
                        "is_metal": False,
                        "is_gap_direct": True,
                        "is_stable": True,
                        "decomposes_to": None
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            # Call function
            result = fetch_materials_project_compositions(
                api_key="test_key",
                base_url="https://api.materialsproject.org",
                limit=10
            )
            
            # Verify
            assert len(result) == 1
            assert result[0]["material_id"] == "mp-12345"
            assert result[0]["formula_pretty"] == "Fe2O3"
            mock_get.assert_called_once()
    
    def test_fetch_handles_empty_response(self):
        """Test fetching when API returns empty data."""
        with patch('scripts.ingest_mp.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_get.return_value = mock_response
            
            result = fetch_materials_project_compositions(
                api_key="test_key",
                base_url="https://api.materialsproject.org"
            )
            
            assert len(result) == 0
    
    def test_fetch_handles_api_error(self):
        """Test fetching when API returns error."""
        with patch('scripts.ingest_mp.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_get.return_value = mock_response
            
            # Should not raise, just return empty list
            result = fetch_materials_project_compositions(
                api_key="test_key",
                base_url="https://api.materialsproject.org"
            )
            
            assert len(result) == 0
    
    def test_fetch_handles_timeout(self):
        """Test fetching when request times out."""
        with patch('scripts.ingest_mp.requests.get') as mock_get:
            mock_get.side_effect = Exception("Timeout")
            
            result = fetch_materials_project_compositions(
                api_key="test_key",
                base_url="https://api.materialsproject.org"
            )
            
            assert len(result) == 0


class TestFetchMaterialsProjectElements:
    """Tests for the fetch_materials_project_elements function."""
    
    def test_fetch_elements(self):
        """Test fetching elemental properties."""
        with patch('scripts.ingest_mp.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [
                    {
                        "element": "Fe",
                        "atomic_number": 26,
                        "atomic_mass": 55.845,
                        "atomic_radius": 156.0,
                        "electronegativity": 1.83,
                        "number_of_valence_electrons": 8
                    },
                    {
                        "element": "O",
                        "atomic_number": 8,
                        "atomic_mass": 15.999,
                        "atomic_radius": 60.0,
                        "electronegativity": 3.44,
                        "number_of_valence_electrons": 6
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            result = fetch_materials_project_elements(
                api_key="test_key",
                base_url="https://api.materialsproject.org"
            )
            
            assert "Fe" in result
            assert "O" in result
            assert result["Fe"]["atomic_number"] == 26
            assert result["O"]["electronegativity"] == 3.44

class TestProcessMpData:
    """Tests for the process_mp_data function."""
    
    def test_process_basic_composition(self):
        """Test processing a basic composition."""
        compositions = [
            {
                "material_id": "mp-12345",
                "formula_pretty": "Fe2O3",
                "formula_anonymous": "A2B3",
                "nelements": 2,
                "nsites": 5,
                "energy_per_atom": -5.2,
                "formation_energy_per_atom": -2.1,
                "band_gap": 0.0,
                "is_metal": False,
                "is_gap_direct": True,
                "is_stable": True,
                "decomposes_to": None
            }
        ]
        
        element_properties = {
            "Fe": {"atomic_radius": 156.0, "electronegativity": 1.83},
            "O": {"atomic_radius": 60.0, "electronegativity": 3.44}
        }
        
        df = process_mp_data(compositions, element_properties)
        
        assert len(df) == 1
        assert df.iloc[0]["composition"] == "Fe2O3"
        assert df.iloc[0]["source"] == "Materials Project"
        assert df.iloc[0]["phase"] == "stable_crystalline"
        assert "Fe" in df.iloc[0]["element_composition"]
    
    def test_process_metallic_composition(self):
        """Test processing a metallic composition."""
        compositions = [
            {
                "material_id": "mp-67890",
                "formula_pretty": "Cu",
                "formula_anonymous": "A",
                "nelements": 1,
                "nsites": 1,
                "energy_per_atom": -3.5,
                "formation_energy_per_atom": 0.0,
                "band_gap": 0.0,
                "is_metal": True,
                "is_gap_direct": False,
                "is_stable": True,
                "decomposes_to": None
            }
        ]
        
        element_properties = {
            "Cu": {"atomic_radius": 128.0, "electronegativity": 1.90}
        }
        
        df = process_mp_data(compositions, element_properties)
        
        assert len(df) == 1
        assert df.iloc[0]["phase"] == "crystalline"
        assert df.iloc[0]["is_metal"] is True
    
    def test_process_unstable_composition(self):
        """Test processing an unstable composition."""
        compositions = [
            {
                "material_id": "mp-11111",
                "formula_pretty": "X",
                "formula_anonymous": "A",
                "nelements": 1,
                "nsites": 1,
                "energy_per_atom": 10.0,
                "formation_energy_per_atom": 5.0,
                "band_gap": 0.0,
                "is_metal": False,
                "is_gap_direct": False,
                "is_stable": False,
                "decomposes_to": ["mp-22222"]
            }
        ]
        
        element_properties = {
            "X": {"atomic_radius": 100.0, "electronegativity": 2.0}
        }
        
        df = process_mp_data(compositions, element_properties)
        
        assert len(df) == 1
        assert df.iloc[0]["phase"] == "unstable"
    
    def test_process_empty_compositions(self):
        """Test processing empty compositions list."""
        df = process_mp_data([], {})
        
        assert len(df) == 0
        assert isinstance(df, pd.DataFrame)
    
    def test_process_formula_parsing(self):
        """Test that formula parsing correctly extracts elements."""
        compositions = [
            {
                "material_id": "mp-99999",
                "formula_pretty": "Zr2CuAl",
                "formula_anonymous": "A2BC",
                "nelements": 3,
                "nsites": 4,
                "energy_per_atom": -4.0,
                "formation_energy_per_atom": -1.5,
                "band_gap": 0.0,
                "is_metal": True,
                "is_gap_direct": False,
                "is_stable": True,
                "decomposes_to": None
            }
        ]
        
        element_properties = {
            "Zr": {"atomic_radius": 160.0, "electronegativity": 1.33},
            "Cu": {"atomic_radius": 128.0, "electronegativity": 1.90},
            "Al": {"atomic_radius": 143.0, "electronegativity": 1.61}
        }
        
        df = process_mp_data(compositions, element_properties)
        
        assert len(df) == 1
        element_comp = json.loads(df.iloc[0]["element_composition"])
        assert "Zr" in element_comp
        assert "Cu" in element_comp
        assert "Al" in element_comp
        assert element_comp["Zr"] == 2
        assert element_comp["Cu"] == 1
        assert element_comp["Al"] == 1

class TestConfigLoading:
    """Tests for configuration loading."""
    
    def test_get_api_key(self):
        """Test that API key is loaded correctly."""
        # This test will pass if the config module loads without error
        # The actual value depends on environment setup
        api_key = get_materials_project_api_key()
        # Just verify it returns a string (may be empty if not set)
        assert isinstance(api_key, str)
