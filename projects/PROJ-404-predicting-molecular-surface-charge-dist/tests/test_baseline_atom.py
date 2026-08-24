"""
Tests for the Atom-Type Average Baseline Model.
"""

import torch
from torch.utils.data import DataLoader, TensorDataset
from models.baseline_atom import AtomTypeAverageBaseline, create_atom_baseline_model
from data.dataset import MoleculeData


def test_fit_computes_correct_means():
    """Test that the fit method correctly computes mean charges per atomic number."""
    # Create synthetic data:
    # Molecule 1: 2 Hydrogens (Z=1), charges [0.1, 0.3] -> Mean for Z=1: 0.2
    # Molecule 2: 1 Carbon (Z=6), charge [0.4] -> Mean for Z=6: 0.4
    # Molecule 3: 1 Hydrogen (Z=1), charge [0.2] -> Combined Mean for Z=1: (0.1+0.3+0.2)/3 = 0.2
    
    # We will simulate a DataLoader with MoleculeData objects
    # Since MoleculeData expects specific attributes, we'll construct them manually
    
    # Batch 1
    x1 = torch.tensor([1, 1, 6]) # H, H, C
    y1 = torch.tensor([0.1, 0.3, 0.4])
    data1 = MoleculeData(x=x1, y=y1)
    
    # Batch 2
    x2 = torch.tensor([1]) # H
    y2 = torch.tensor([0.2])
    data2 = MoleculeData(x=x2, y=y2)

    dataset = [data1, data2]
    loader = DataLoader(dataset, batch_size=1)

    model = create_atom_baseline_model()
    model.fit(loader)

    # Assertions
    assert 1 in model.atomic_mean_charges
    assert 6 in model.atomic_mean_charges
    
    # Mean for Z=1: (0.1 + 0.3 + 0.2) / 3 = 0.2
    assert abs(model.atomic_mean_charges[1] - 0.2) < 1e-5
    # Mean for Z=6: 0.4
    assert abs(model.atomic_mean_charges[6] - 0.4) < 1e-5


def test_forward_predicts_correct_values():
    """Test that forward pass returns correct mean charges for given atomic numbers."""
    # Pre-computed means
    means = {1: 0.5, 6: 1.0, 8: 2.0}
    model = create_atom_baseline_model(atomic_mean_charges=means)

    # Input: H, C, O, H
    x = torch.tensor([1, 6, 8, 1])
    data = MoleculeData(x=x, y=torch.zeros(4)) # y shape doesn't matter for input, just x

    predictions = model.forward(data)

    expected = torch.tensor([0.5, 1.0, 2.0, 0.5])
    
    assert torch.allclose(predictions, expected)


def test_forward_unseen_atom_type_defaults_to_zero():
    """Test that unseen atomic numbers default to 0.0."""
    means = {1: 0.5} # Only Hydrogen seen
    model = create_atom_baseline_model(atomic_mean_charges=means)

    # Input: H, C (Carbon unseen)
    x = torch.tensor([1, 6])
    data = MoleculeData(x=x, y=torch.zeros(2))

    predictions = model.forward(data)

    # Expected: 0.5 for H, 0.0 for C
    expected = torch.tensor([0.5, 0.0])
    assert torch.allclose(predictions, expected)


def test_fit_raises_error_if_empty_loader():
    """Test that fitting on empty data raises appropriate error or leaves dict empty."""
    model = create_atom_baseline_model()
    loader = DataLoader([])
    model.fit(loader)
    # Should result in empty dict
    assert model.atomic_mean_charges == {}


def test_forward_raises_if_not_fitted():
    """Test that forward raises RuntimeError if model hasn't been fitted."""
    model = create_atom_baseline_model()
    x = torch.tensor([1])
    data = MoleculeData(x=x, y=torch.zeros(1))

    try:
        model.forward(data)
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "has not been fitted" in str(e)
