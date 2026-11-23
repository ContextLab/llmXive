import os
import sys
import pytest
import pandas as pd
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.valence_calculation import ValenceCalculationError

class TestValenceSwitchLogic:
    def test_valence_switch_coverage_check(self):
        # This tests the logic that would be in the main function
        # We mock the coverage calculation to force a switch
        tokens = ["unknown"] * 100
        nrc_lexicon = {} # Empty lexicon to force 0% coverage
        
        from utils.valence_calculation import calculate_nrc_coverage
        coverage = calculate_nrc_coverage(tokens, nrc_lexicon)
        
        assert coverage == 0.0
        assert coverage < 0.5 # Should trigger switch

    def test_valence_switch_no_switch(self):
        tokens = ["happy", "sad"] * 50
        nrc_lexicon = {"happy": 1, "sad": 1}
        
        from utils.valence_calculation import calculate_nrc_coverage
        coverage = calculate_nrc_coverage(tokens, nrc_lexicon)
        
        assert coverage == 1.0
        assert coverage >= 0.5 # Should not switch
