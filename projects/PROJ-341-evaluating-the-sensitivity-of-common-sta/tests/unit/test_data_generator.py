import pytest
import numpy as np
from code.simulation.data_generator import generate_normal_data, generate_multinomial_data, validate_distribution_params

def test_generate_normal_data():
    data = generate_normal_data(100, mean=5, std=2, seed=42)
    assert len(data) == 100
    assert np.isclose(data.mean(), 5, atol=1)
    assert np.isclose(data.std(), 2, atol=1)

def test_generate_multinomial_data():
    data = generate_multinomial_data(10, [0.5, 0.5], seed=42)
    assert len(data) == 2
    assert sum(data) == 10

def test_validate_distribution_params():
    assert validate_distribution_params('normal', {'mean': 0, 'std': 1})
    assert not validate_distribution_params('normal', {'mean': 0})
    assert validate_distribution_params('multinomial', {'probs': [0.5, 0.5]})
    assert not validate_distribution_params('multinomial', {'probs': [0.6, 0.6]})

if __name__ == '__main__':
    pytest.main([__file__])
