import unittest
import pandas as pd
from pathlib import Path
import sys

# Add path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.analysis.fit_models import filter_zero_kloc

class TestZeroKlocExclusion(unittest.TestCase):
    
    def test_zero_kloc_exclusion(self):
        """Verify rows with kloc=0 are excluded."""
        data = {
            "url": ["a", "b", "c"],
            "kloc": [10.0, 0.0, 5.0],
            "cve_count": [1, 0, 2]
        }
        df = pd.DataFrame(data)
        
        filtered_df = filter_zero_kloc(df)
        
        self.assertEqual(len(filtered_df), 2)
        self.assertTrue(filtered_df["kloc"].gt(0).all())