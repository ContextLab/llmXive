import pandas as pd
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocessing import classify_alloy_family

class TestAlloyClassification:
    def test_high_entropy_alloy(self):
        """Test rule: 5+ elements > 5% each -> High-Entropy Alloy"""
        # Fe=20, Cr=20, Ni=20, Co=20, Mn=20 (5 elements > 5%)
        row = pd.Series({
            'Fe': 20.0, 'Cr': 20.0, 'Ni': 20.0, 'Co': 20.0, 'Mn': 20.0,
            'C': 0.1, 'Si': 0.5
        })
        assert classify_alloy_family(row) == "High-Entropy Alloy"

    def test_stainless_steel(self):
        """Test rule: Fe > 10% AND Cr > 10% -> Stainless Steel"""
        # Fe=15, Cr=15 (Fe > 10, Cr > 10)
        # Not HEA (only 2 elements > 5%)
        row = pd.Series({
            'Fe': 15.0, 'Cr': 15.0, 'Ni': 5.0, 'C': 0.1
        })
        assert classify_alloy_family(row) == "Stainless Steel"

    def test_carbon_steel(self):
        """Test rule: Fe > 80% AND C < 2% -> Carbon Steel"""
        # Fe=85, C=0.5
        row = pd.Series({
            'Fe': 85.0, 'C': 0.5, 'Mn': 1.0
        })
        assert classify_alloy_family(row) == "Carbon Steel"

    def test_other(self):
        """Test default rule: Other"""
        # Fe=5, Cr=5 (Does not meet Fe>10 or Fe>80)
        row = pd.Series({
            'Fe': 5.0, 'Cr': 5.0, 'Ni': 5.0
        })
        assert classify_alloy_family(row) == "Other"

    def test_edge_case_fe_10(self):
        """Test boundary: Fe exactly 10% should NOT trigger Stainless Steel if Cr is high"""
        # Fe=10, Cr=15 -> Fe is not > 10, so should not be Stainless Steel
        row = pd.Series({
            'Fe': 10.0, 'Cr': 15.0
        })
        assert classify_alloy_family(row) != "Stainless Steel"

    def test_edge_case_fe_80(self):
        """Test boundary: Fe exactly 80% should NOT trigger Carbon Steel"""
        # Fe=80, C=0.5 -> Fe is not > 80
        row = pd.Series({
            'Fe': 80.0, 'C': 0.5
        })
        assert classify_alloy_family(row) != "Carbon Steel"
