import unittest
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from code.data.fetch_thermo_proxy import fetch_thermo_proxy, validate_ternary_parameters

class TestFetchThermoProxy(unittest.TestCase):

    @patch('code.data.fetch_thermo_proxy.urlretrieve')
    def test_fetch_thermo_proxy_success(self, mock_urlretrieve):
        mock_urlretrieve.return_value = None  # Simulate successful download
        filepath = Path("data/raw/TCFE.tdb")
        self.assertTrue(fetch_thermo_proxy("http://example.com/tcfetdb", filepath))

    @patch('code.data.fetch_thermo_proxy.urlretrieve')
    def test_fetch_thermo_proxy_failure(self, mock_urlretrieve):
        mock_urlretrieve.side_effect = Exception("Download failed")  # Simulate download failure
        filepath = Path("data/raw/TCFE.tdb")
        self.assertFalse(fetch_thermo_proxy("http://example.com/tcfetdb", filepath))

    def test_validate_ternary_parameters_success(self):
        filepath = Path("data/raw/TCFE.tdb")
        # Create a dummy file with all required parameters
        with open(filepath, "w") as f:
            f.write("Fe-Cr\nFe-Mo\nFe-V\nFe-W\nFe-Cr-Mo\nFe-Cr-V\nFe-Mo-V\nFe-Cr-W\nFe-Mo-W")

        self.assertTrue(validate_ternary_parameters(filepath))
    
    def test_validate_ternary_parameters_missing(self):
      filepath = Path("data/raw/TCFE.tdb")
      with open(filepath, "w") as f:
          f.write("Fe-Cr\nFe-Mo\nFe-V\nFe-W") # Missing ternary systems
      with self.assertRaisesRegex(ValueError, "Missing ternary parameters for systems:"):
        validate_ternary_parameters(filepath)

if __name__ == '__main__':
    unittest.main()