import os
import sys
import unittest
from pathlib import Path

class TestAmendmentContent(unittest.TestCase):
    """
    Unit test to verify the content of the Spec Amendment artifact.
    This ensures the artifact explicitly states the required pivots and changes.
    """

    def setUp(self):
        self.amendment_path = Path("specs/amendment-001-fluid-intelligence-n10.md")
        if not self.amendment_path.exists():
            self.skipTest("Amendment file not found; skipping content verification.")
        
        with open(self.amendment_path, "r") as f:
            self.content = f.read()

    def test_fr001_pivot_to_fluid_intelligence(self):
        """Verify FR-001 is amended to pivot to Fluid Intelligence and remove Musical Creativity halt."""
        self.assertIn("FR-001", self.content)
        self.assertIn("Fluid Intelligence", self.content)
        self.assertIn("Musical Creativity", self.content) # Mentioned as removed
        self.assertIn("REMOVED", self.content)
        self.assertIn("No valid Fluid Intelligence data found", self.content)

    def test_sc001_sc005_n10_baseline(self):
        """Verify SC-001 and SC-005 are amended to reflect N=10 CI feasibility baseline."""
        self.assertIn("SC-001", self.content)
        self.assertIn("SC-005", self.content)
        self.assertIn("N=10", self.content)
        self.assertIn("CI feasibility", self.content)
        self.assertIn("N=50", self.content) # Mentioned as original/removed context

    def test_fr005_sc004_bonferroni_mandate(self):
        """Verify FR-005 and SC-004 are amended to mandate Bonferroni correction."""
        self.assertIn("FR-005", self.content)
        self.assertIn("SC-004", self.content)
        self.assertIn("Bonferroni", self.content)
        self.assertIn("FDR", self.content) # Mentioned as removed
        self.assertIn("Constitution Principle VII", self.content)

    def test_governance_authority(self):
        """Verify the document states it is the ratified authority."""
        self.assertIn("RATIFIED", self.content)
        self.assertIn("Authority", self.content)

if __name__ == "__main__":
    unittest.main()