"""
Unit tests for Power Analysis (T036).
"""
import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.analysis.power_analysis import PowerCalculator

class TestPowerCalculator:
    @pytest.fixture
    def small_df(self):
        """Create a small dataframe (N=10) to test UNDERPOWERED flag."""
        data = {
            'participant_id': [f'P{i}' for i in range(10)],
            'disability_type': ['visual'] * 5 + ['motor'] * 5,
            'sequence': ['trad_exp'] * 5 + ['exp_trad'] * 5
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def large_df(self):
        """Create a large dataframe (N=50) to test OK flag."""
        n = 50
        data = {
            'participant_id': [f'P{i}' for i in range(n)],
            'disability_type': ['visual'] * 25 + ['motor'] * 25,
            'sequence': ['trad_exp'] * 25 + ['exp_trad'] * 25
        }
        return pd.DataFrame(data)

    def test_calculate_power_rm_anova_small_n(self, small_df):
        """Test power calculation with small N returns low power."""
        calc = PowerCalculator()
        # N=10, effect_size=0.06 (small)
        power = calc.calculate_power_rm_anova(n=10, effect_size=0.06)
        # With N=10 and small effect, power should be very low
        assert power < 0.5

    def test_calculate_power_rm_anova_large_n(self, large_df):
        """Test power calculation with large N returns higher power."""
        calc = PowerCalculator()
        # N=50, effect_size=0.06
        power = calc.calculate_power_rm_anova(n=50, effect_size=0.06)
        # Power should be higher than small N case
        assert power > 0.1

    def test_analyze_power_flags_underpowered(self, small_df):
        """Test that N < 30 is flagged as UNDERPOWERED."""
        calc = PowerCalculator()
        results = calc.analyze_power(small_df, effect_size=0.06)
        
        total_flag = [r for r in results if r['subgroup'] == 'Total Sample'][0]
        assert total_flag['flag'] == 'UNDERPOWERED'
        assert total_flag['N'] == 10

    def test_analyze_power_ok_for_large(self, large_df):
        """Test that N >= 30 is evaluated, potentially OK if power > 0.8."""
        calc = PowerCalculator()
        results = calc.analyze_power(large_df, effect_size=0.2) # Use larger effect for OK flag
        
        total_flag = [r for r in results if r['subgroup'] == 'Total Sample'][0]
        assert total_flag['N'] == 50
        # With N=50 and effect=0.2, power should be decent
        # We just assert it's not flagged as UNDERPOWERED due to N < 30
        assert total_flag['flag'] != 'UNDERPOWERED' or total_flag.get('power', 0) >= 0.8

    def test_subgroup_disability_underpowered(self, small_df):
        """Test subgroup analysis flags small disability groups."""
        calc = PowerCalculator()
        results = calc.analyze_power(small_df)
        
        disability_flags = [r for r in results if r['subgroup'].startswith('Disability:')]
        assert len(disability_flags) == 2 # visual, motor
        for flag in disability_flags:
            assert flag['flag'] == 'UNDERPOWERED'
            assert flag['N'] == 5

    def test_output_structure(self, small_df):
        """Test the structure of the output dictionary."""
        calc = PowerCalculator()
        results = calc.analyze_power(small_df)
        
        required_keys = {'subgroup', 'N', 'flag', 'message'}
        for item in results:
            assert required_keys.issubset(item.keys())
            assert isinstance(item['N'], int)
            assert isinstance(item['flag'], str)
            assert item['flag'] in ['UNDERPOWERED', 'OK']