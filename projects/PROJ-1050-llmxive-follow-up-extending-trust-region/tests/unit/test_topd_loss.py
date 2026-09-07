"""
Unit tests for the TOP-D Loss function.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from student.topd_loss import TOPDLoss

@pytest.fixture
def loss_fn():
    """Create a test loss function."""
    return TOPDLoss(temperature=1.0, kl_weight=0.5)

def test_topd_loss_calculation(loss_fn):
    """Test TOP-D loss calculation with alpha interpolation."""
    state = np.random.randn(10)
    teacher_action = np.zeros(5)
    teacher_action[2] = 1.0
    student_action = np.zeros(5)
    student_action[1] = 1.0
    
    # Test with alpha = 0.0 (pure student)
    loss_0 = loss_fn.compute_loss(state, teacher_action, student_action, alpha=0.0)
    assert isinstance(loss_0, float)
    assert loss_0 >= 0
    
    # Test with alpha = 1.0 (pure teacher)
    loss_1 = loss_fn.compute_loss(state, teacher_action, student_action, alpha=1.0)
    assert isinstance(loss_1, float)
    assert loss_1 >= 0
    
    # Test with alpha = 0.5 (mixed)
    loss_05 = loss_fn.compute_loss(state, teacher_action, student_action, alpha=0.5)
    assert isinstance(loss_05, float)
    assert loss_05 >= 0

def test_topd_loss_alpha_bounds(loss_fn):
    """Test that alpha bounds are enforced."""
    state = np.random.randn(10)
    teacher_action = np.zeros(5)
    teacher_action[2] = 1.0
    student_action = np.zeros(5)
    student_action[1] = 1.0
    
    # Test invalid alpha
    with pytest.raises(ValueError):
        loss_fn.compute_loss(state, teacher_action, student_action, alpha=-0.1)
    
    with pytest.raises(ValueError):
        loss_fn.compute_loss(state, teacher_action, student_action, alpha=1.1)

def test_topd_loss_components(loss_fn):
    """Test that loss components are correctly calculated."""
    state = np.random.randn(10)
    teacher_action = np.zeros(5)
    teacher_action[2] = 1.0
    student_action = np.zeros(5)
    student_action[1] = 1.0
    
    components = loss_fn.get_loss_components(state, teacher_action, student_action, alpha=0.5)
    
    assert "student_loss" in components
    assert "kl_divergence" in components
    assert "interpolated_loss" in components
    assert all(isinstance(v, float) for v in components.values())

if __name__ == "__main__":
    pytest.main([__file__, "-v"])