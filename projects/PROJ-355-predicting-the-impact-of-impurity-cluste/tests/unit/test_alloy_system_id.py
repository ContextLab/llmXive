import unittest
from pathlib import Path
import tempfile
import json
from unittest.mock import MagicMock, patch

# Import the function to test
from code.data.descriptors import extract_alloy_system_id, generate_alloy_systems_report

class TestAlloySystemId(unittest.TestCase):

    def test_extract_alloy_system_id_fcc(self):
        """Test extraction for an FCC-like structure (simulated)."""
        # Mock structure to simulate FCC (Fm-3m)
        mock_structure = MagicMock()
        mock_structure.lattice.abc = (3.0, 3.0, 3.0)
        mock_structure.lattice.angles = (90.0, 90.0, 90.0)
        
        # We need to mock the SpaceGroupAnalyzer behavior
        with patch('code.data.descriptors.SpaceGroupAnalyzer') as MockSGA:
            mock_sga_instance = MagicMock()
            mock_sga_instance.get_space_group_symbol.return_value = "Fm-3m"
            mock_sga_instance.get_crystal_system.return_value = "cubic"
            MockSGA.return_value = mock_sga_instance
            
            result = extract_alloy_system_id(mock_structure, "Cr")
            
            self.assertEqual(result, "FCC_Cr")

    def test_extract_alloy_system_id_bcc(self):
        """Test extraction for a BCC-like structure (simulated)."""
        mock_structure = MagicMock()
        mock_structure.lattice.abc = (3.0, 3.0, 3.0)
        mock_structure.lattice.angles = (90.0, 90.0, 90.0)
        
        with patch('code.data.descriptors.SpaceGroupAnalyzer') as MockSGA:
            mock_sga_instance = MagicMock()
            mock_sga_instance.get_space_group_symbol.return_value = "Im-3m"
            mock_sga_instance.get_crystal_system.return_value = "cubic"
            MockSGA.return_value = mock_sga_instance
            
            result = extract_alloy_system_id(mock_structure, "Fe")
            
            self.assertEqual(result, "BCC_Fe")

    def test_generate_alloy_systems_report(self):
        """Test the generation of the alloy_systems.json file."""
        # Create mock data
        mock_structure_fcc = MagicMock()
        mock_structure_bcc = MagicMock()
        
        test_data = [
            {
                "structure": mock_structure_fcc,
                "impurity_species": "Cr",
                "index": 0
            },
            {
                "structure": mock_structure_bcc,
                "impurity_species": "Ni",
                "index": 1
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "alloy_systems.json"
            
            with patch('code.data.descriptors.SpaceGroupAnalyzer') as MockSGA:
                mock_sga_instance = MagicMock()
                # First call for FCC, second for BCC
                def side_effect(*args, **kwargs):
                    # We need to track which structure is being analyzed
                    # Since we can't easily distinguish mocks, we'll assume the logic
                    # in the function handles it or we mock the return value globally
                    # For this test, we'll just ensure the function runs and produces output
                    # We'll force the first to be FCC and second to be BCC by manipulating the mock
                    # Actually, simpler: just mock the return value to be consistent for the test
                    # or use a counter.
                    return mock_sga_instance
                
                mock_sga_instance.get_space_group_symbol.side_effect = ["Fm-3m", "Im-3m"]
                mock_sga_instance.get_crystal_system.side_effect = ["cubic", "cubic"]
                MockSGA.return_value = mock_sga_instance

                generate_alloy_systems_report(test_data, output_path)
                
                self.assertTrue(output_path.exists())
                
                with open(output_path, 'r') as f:
                    data = json.load(f)
                
                self.assertEqual(len(data), 2)
                self.assertEqual(data[0]["alloy_system_id"], "FCC_Cr")
                self.assertEqual(data[1]["alloy_system_id"], "BCC_Ni")
                self.assertEqual(data[0]["crystal_system"], "FCC")
                self.assertEqual(data[1]["crystal_system"], "BCC")

if __name__ == "__main__":
    unittest.main()
