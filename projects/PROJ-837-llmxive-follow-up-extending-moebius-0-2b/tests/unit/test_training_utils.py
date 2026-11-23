import pytest
import torch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from training.train_gating import MultiTaskLoss
from training.train_end_to_end import compute_reconstruction_loss

class TestTrainingUtils:
    def test_reconstruction_loss_mse(self):
        """Test MSE reconstruction loss"""
        pred = torch.randn(2, 3, 32, 32)
        target = torch.randn(2, 3, 32, 32)
        
        loss = compute_reconstruction_loss(pred, target, method='mse')
        
        assert loss >= 0
        assert torch.isfinite(loss)

    def test_reconstruction_loss_l1(self):
        """Test L1 reconstruction loss"""
        pred = torch.randn(2, 3, 32, 32)
        target = torch.randn(2, 3, 32, 32)
        
        loss = compute_reconstruction_loss(pred, target, method='l1')
        
        assert loss >= 0
        assert torch.isfinite(loss)

    def test_multitask_loss_creation(self):
        """Test MultiTaskLoss creation"""
        loss_fn = MultiTaskLoss(
            reconstruction_weight=1.0,
            regression_weight=0.1,
            rank_weight=0.1
        )
        assert loss_fn is not None

    def test_multitask_loss_compute(self):
        """Test MultiTaskLoss computation"""
        loss_fn = MultiTaskLoss(
            reconstruction_weight=1.0,
            regression_weight=0.1,
            rank_weight=0.1
        )
        
        pred_img = torch.randn(2, 3, 32, 32)
        target_img = torch.randn(2, 3, 32, 32)
        pred_score = torch.randn(2, 1)
        target_score = torch.randn(2, 1)
        pred_rank = torch.randint(1, 6, (2,))
        target_rank = torch.randint(1, 6, (2,))
        
        total_loss, components = loss_fn(
            pred_img, target_img,
            pred_score, target_score,
            pred_rank, target_rank
        )
        
        assert total_loss >= 0
        assert torch.isfinite(total_loss)
        assert 'reconstruction' in components
        assert 'regression' in components
        assert 'rank' in components

    def test_multitask_loss_weights(self):
        """Test that loss weights are applied correctly"""
        loss_fn = MultiTaskLoss(
            reconstruction_weight=2.0,
            regression_weight=0.5,
            rank_weight=0.5
        )
        
        pred_img = torch.ones(2, 3, 32, 32)
        target_img = torch.zeros(2, 3, 32, 32)
        pred_score = torch.ones(2, 1)
        target_score = torch.zeros(2, 1)
        pred_rank = torch.ones(2, dtype=torch.long)
        target_rank = torch.zeros(2, dtype=torch.long)
        
        total_loss, components = loss_fn(
            pred_img, target_img,
            pred_score, target_score,
            pred_rank, target_rank
        )
        
        # Reconstruction should dominate
        assert components['reconstruction'] > components['regression']
        assert components['reconstruction'] > components['rank']

    def test_reconstruction_loss_zero(self):
        """Test reconstruction loss is zero for identical inputs"""
        x = torch.randn(2, 3, 32, 32)
        
        loss = compute_reconstruction_loss(x, x, method='mse')
        assert loss < 1e-6