import pytest
from analysis.power import run_power_analysis

def test_power_analysis(tmp_path):
    # Minimal parameters for power analysis
    result = run_power_analysis(num_games=1000, effect_size=0.5, alpha=0.05)
    assert result is not None
