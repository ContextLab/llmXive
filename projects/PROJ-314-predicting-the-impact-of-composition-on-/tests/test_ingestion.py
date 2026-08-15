import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from code.ingestion import validate_entry, derive_primary_anion_cation_group

class TestIngestion(unittest.TestCase):
    def test_validate_entry(self):
        valid_entry = {'composition': 'Al2O3', 'weibull_modulus': 10.0, 'sample_count': 50}
        self.assertTrue(validate_entry(valid_entry))
        
        invalid_entry = {'composition': 'Al2O3'}
        self.assertFalse(validate_entry(invalid_entry))

    def test_derive_primary_anion_cation_group(self):
        group = derive_primary_anion_cation_group("Al2O3")
        self.assertIn("O", group)
        self.assertIn("Al", group)

if __name__ == "__main__":
    unittest.main()
