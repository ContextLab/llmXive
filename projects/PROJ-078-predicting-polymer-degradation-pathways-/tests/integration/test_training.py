"""Integration tests for training loop convergence."""
import pytest
import torch
from torch_geometric.data import Data
from model import PolymerGNN

class TestTrainingConvergence:
    @pytest.mark.slow
    def test_training_converges_cpu(self):
        """
        Test that the training loop converges on CPU within a reasonable time.
        This is a simplified convergence check for the integration test.
        """
        # Create dummy data
        x = torch.randn(20, 10)
        edge_index = torch.randint(0, 20, (2, 50))
        y = torch.randint(0, 2, (20,))
        data = Data(x=x, edge_index=edge_index, y=y)

        # Initialize model
        model = PolymerGNN(input_dim=10, hidden_dim=16, num_layers=2, output_dim=2)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        criterion = torch.nn.CrossEntropyLoss()

        # Simple training loop
        model.train()
        initial_loss = None
        final_loss = None

        for epoch in range(10):  # Short run for testing
            optimizer.zero_grad()
            out = model(data)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()

            if epoch == 0:
                initial_loss = loss.item()
            final_loss = loss.item()

        # Check if loss decreased (convergence heuristic)
        # Note: This is a basic check; real tests would use validation metrics
        assert final_loss < initial_loss, f"Loss did not decrease: {initial_loss} -> {final_loss}"
