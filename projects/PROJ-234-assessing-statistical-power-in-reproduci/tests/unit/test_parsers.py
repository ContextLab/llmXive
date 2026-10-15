import pytest
from code.utils.parsers import extract_sample_size, extract_effect_size

def test_extract_sample_size():
    assert extract_sample_size("The sample size was N=150.") == 150
    assert extract_sample_size("N = 200 participants") == 200
    assert extract_sample_size("n=50") is None # Case sensitive per regex r"N\s*=\s*(\d+)"
    assert extract_sample_size("No sample size here") is None

def test_extract_cohens_d():
    # Test full name
    val, metric, dof = extract_effect_size("We observed Cohen's d = 0.85 in the group.")
    assert val == 0.85
    assert metric == "Cohen's d"
    assert dof is None
    
    # Test shorthand
    val, metric, dof = extract_effect_size("The effect was d=0.21.")
    assert val == 0.21
    assert metric == "Cohen's d"
    
    # Test negative value
    val, metric, dof = extract_effect_size("Cohen's d = -0.4")
    assert val == -0.4

def test_extract_f_statistic():
    # Standard F(df1, df2) = val
    val, metric, dof = extract_effect_size("The result was significant, F(2, 145) = 4.56.")
    assert val == 4.56
    assert metric == "F"
    assert dof == (2, 145)
    
    # F with spaces
    val, metric, dof = extract_effect_size("F ( 1 , 20 ) = 12.3")
    assert val == 12.3
    assert dof == (1, 20)

def test_parsers_no_match():
    val, metric, dof = extract_effect_size("No stats here.")
    assert val is None
    assert metric is None
    assert dof is None