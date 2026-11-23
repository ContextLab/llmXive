import unittest
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pipeline.trainer import count_flops, train_epoch, run_training_cycle

class DummyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear1 = nn.Linear(10, 20)
        self.relu = nn.ReLU()
        self.linear2 = nn.Linear(20, 5)
    
    def forward(self, x):
        x = self.linear1(x)
        x = self.relu(x)
        x = self.linear2(x)
        return x

class TestTrainer(unittest.TestCase):

    def test_count_flops_linear(self):
        """
        Test FLOP counting for a simple Linear layer.
        Model: Linear(10, 20) -> ReLU -> Linear(20, 5)
        Input: (batch=1, seq=1, hidden=10) -> (1, 1, 20) -> (1, 1, 5)
        
        FLOPs for Linear(10, 20) with input (1, 1, 10):
        2 * 1 * 1 * 10 * 20 = 400
        FLOPs for Linear(20, 5) with input (1, 1, 20):
        2 * 1 * 1 * 20 * 5 = 200
        Total = 600
        """
        model = DummyModel()
        input_shape = (1, 1, 10) # (batch, seq, hidden)
        
        flops = count_flops(model, input_shape)
        
        # Expected: 2 * 1 * 1 * 10 * 20 + 2 * 1 * 1 * 20 * 5 = 400 + 200 = 600
        expected_flops = 600
        
        self.assertEqual(flops, expected_flops)

    def test_count_flops_batch(self):
        """
        Test FLOP counting with a larger batch size.
        Input: (batch=4, seq=2, hidden=10)
        Linear(10, 20): 2 * 4 * 2 * 10 * 20 = 3200
        Linear(20, 5): 2 * 4 * 2 * 20 * 5 = 1600
        Total = 4800
        """
        model = DummyModel()
        input_shape = (4, 2, 10)
        
        flops = count_flops(model, input_shape)
        expected_flops = 4800
        
        self.assertEqual(flops, expected_flops)

    def test_train_epoch_loss_decreases(self):
        """
        Unit test for train_epoch: asserts loss decreases over epochs on mock data.
        """
        # Create a simple dataset where loss should decrease with training
        # We'll use a linear relationship with noise
        torch.manual_seed(42)
        X = torch.randn(100, 10)
        y = torch.sum(X, dim=1, keepdim=True) + torch.randn(100, 1) * 0.1
        
        dataset = TensorDataset(X, y)
        dataloader = DataLoader(dataset, batch_size=10)
        
        model = nn.Linear(10, 1)
        optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
        criterion = nn.MSELoss()
        device = torch.device('cpu')
        
        # Train for a few epochs
        losses = []
        for i in range(5):
            epoch_loss = train_epoch(model, dataloader, optimizer, criterion, device, i)
            losses.append(epoch_loss)
        
        # Assert that the loss generally decreases (last loss < first loss)
        # Note: Stochastic gradient descent might have some variance, but with lr=0.1 and simple data, it should decrease.
        self.assertLess(losses[-1], losses[0], "Loss should decrease after training")

    def test_run_training_cycle(self):
        """
        Test the run_training_cycle function.
        """
        torch.manual_seed(42)
        X = torch.randn(50, 5)
        y = torch.sum(X, dim=1, keepdim=True)
        
        dataset = TensorDataset(X, y)
        dataloader = DataLoader(dataset, batch_size=10)
        
        model = nn.Linear(5, 1)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        criterion = nn.MSELoss()
        device = torch.device('cpu')
        
        result = run_training_cycle(model, dataloader, optimizer, criterion, device, epochs=3)
        
        self.assertIn("epoch_losses", result)
        self.assertIn("avg_loss", result)
        self.assertEqual(len(result["epoch_losses"]), 3)
        self.assertIsInstance(result["avg_loss"], float)
