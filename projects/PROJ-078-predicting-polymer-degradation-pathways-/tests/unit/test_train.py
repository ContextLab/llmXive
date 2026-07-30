"""
Unit tests for training module (T028).
Tests k-fold split logic, convergence check, and seed pinning.
"""
import os
import sys
import json
import tempfile
import torch
from torch_geometric.data import Data
import pytest

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from train import (
    set_seed, 
    stratified_k_fold_split, 
    leave_one_out_splits, 
    check_convergence,
    load_graph_data
)

class TestSeedPinning:
    def test_set_seed_reproducibility(self):
        """Verify that setting seed produces deterministic results."""
        set_seed(42)
        a = torch.randn(10)
        
        set_seed(42)
        b = torch.randn(10)
        
        assert torch.equal(a, b), "Seed pinning failed: tensors not equal"

class TestConvergenceCheck:
    def test_convergence_detected(self):
        """Test that stable loss triggers convergence."""
        # Losses that stabilize quickly
        history = [0.5, 0.4, 0.3, 0.2, 0.1, 0.09, 0.085, 0.08]
        # Check last 5: 0.2, 0.1, 0.09, 0.085, 0.08
        # Changes are significant initially, but let's test a truly stable tail
        stable_history = [0.1, 0.099, 0.098, 0.097, 0.096, 0.0955, 0.095]
        # Relative change from 0.096 to 0.0955 is ~0.5%
        assert check_convergence(stable_history, window=5, threshold=0.05) is True

    def test_no_convergence_early(self):
        """Test that volatile loss does not trigger convergence."""
        volatile_history = [1.0, 0.5, 0.9, 0.1, 0.8]
        assert check_convergence(volatile_history, window=3, threshold=0.05) is False

    def test_insufficient_history(self):
        """Test that short history returns False."""
        short_history = [0.5, 0.4]
        assert check_convergence(short_history, window=5) is False

class TestCrossValidationSplits:
    def test_stratified_kfold_balanced(self):
        """Test stratified split with balanced classes."""
        # Create dummy data
        n_samples = 20
        data_list = [Data(x=torch.randn(5)) for _ in range(n_samples)]
        labels = [0] * 10 + [1] * 10
        
        folds = stratified_k_fold_split(data_list, labels, n_splits=2)
        
        assert len(folds) == 2
        for train_idx, val_idx in folds:
            # Check stratification
            train_labels = [labels[i] for i in train_idx]
            val_labels = [labels[i] for i in val_idx]
            
            # Each fold should have roughly equal class distribution
            assert abs(train_labels.count(0) - train_labels.count(1)) <= 2
            assert abs(val_labels.count(0) - val_labels.count(1)) <= 2

    def test_leave_one_out(self):
        """Test LOO splits."""
        n_samples = 5
        data_list = [Data(x=torch.randn(5)) for _ in range(n_samples)]
        labels = [0, 1, 0, 1, 0]
        
        folds = leave_one_out_splits(data_list, labels)
        
        assert len(folds) == n_samples
        for train_idx, val_idx in folds:
            assert len(val_idx) == 1
            assert len(train_idx) == n_samples - 1

class TestLoadGraphData:
    def test_load_valid_csv(self):
        """Test loading a valid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['node_features', 'edge_index', 'label'])
            # Write a simple graph
            writer.writerow([
                json.dumps([[1.0, 0.0], [0.0, 1.0]]),
                json.dumps([[0, 1], [1, 0]]),
                '0'
            ])
            temp_path = f.name

        try:
            data_list, labels = load_graph_data(temp_path)
            assert len(data_list) == 1
            assert labels[0] == 0
            assert data_list[0].x.shape == (2, 2)
        finally:
            os.unlink(temp_path)

    def test_load_missing_file(self):
        """Test that missing file raises error."""
        with pytest.raises(FileNotFoundError):
            load_graph_data("non_existent_file.csv")