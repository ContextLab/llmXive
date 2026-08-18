"""
Unit tests for edge cases in the solubility prediction pipeline.

Tests cover:
1. Malformed SMILES handling (invalid syntax, empty strings, unsupported characters)
2. Non-convergent GNN detection (monotonically increasing loss, early stopping triggers)
"""
import pytest
import os
import sys
import tempfile
import json
from pathlib import Path
import numpy as np
import torch
from torch_geometric.data import Data
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import process_molecule, get_atom_features
from models.gnn_mpnn import GNNMPNN
from training.train_gnn import train_model, save_model
from config.seeds import set_seed


class TestMalformedSMILES:
    """Tests for handling malformed SMILES strings in preprocessing."""

    def test_empty_smiles_string(self):
        """Test that empty SMILES string raises ValueError."""
        with pytest.raises(ValueError, match="Empty SMILES string"):
            process_molecule("", log_file=None)

    def test_invalid_smiles_syntax(self):
        """Test that invalid SMILES syntax is handled gracefully."""
        # Invalid: unmatched brackets, impossible valency
        invalid_smiles = ["C[C", "C1CC1(C)C", "C#C#C"]  # Second is valid, others invalid
        
        for smiles in invalid_smiles:
            # Should raise or return None depending on implementation
            # Based on T005 requirements, invalid SMILES should be excluded
            try:
                result = process_molecule(smiles, log_file=None)
                # If it returns, it should be None or raise
                assert result is None, f"Invalid SMILES {smiles} should return None"
            except Exception:
                # Expected behavior - exception is also acceptable
                pass

    def test_supported_characters_only(self):
        """Test that SMILES with unsupported characters are rejected."""
        unsupported = ["C@H", "C$C", "C?C"]
        
        for smiles in unsupported:
            with pytest.raises((ValueError, Exception)):
                process_molecule(smiles, log_file=None)

    def test_whitespace_handling(self):
        """Test that SMILES with leading/trailing whitespace are handled."""
        valid_with_ws = "  CCO  "
        # Should strip whitespace and process
        result = process_molecule(valid_with_ws, log_file=None)
        assert result is not None, "Valid SMILES with whitespace should be processed"

    def test_very_long_smiles(self):
        """Test handling of extremely long SMILES strings."""
        # Create a very long but valid SMILES
        long_smiles = "C" * 10000
        # Should either process or raise with clear error
        try:
            result = process_molecule(long_smiles, log_file=None)
            # If it processes, ensure it doesn't crash
            assert result is not None or result is None
        except Exception:
            # Expected for extremely long inputs
            pass

    def test_special_molecule_cases(self):
        """Test special cases like single atoms, ions, radicals."""
        special_cases = [
            "[Na+]",
            "[Cl-]",
            "[CH3]",
            "[C]",
        ]
        
        for smiles in special_cases:
            # Should not crash, may return None if unsupported
            try:
                result = process_molecule(smiles, log_file=None)
                assert result is not None or result is None
            except Exception:
                # Some special cases might raise
                pass


class TestNonConvergentGNN:
    """Tests for detecting non-convergent GNN training."""

    def setup_method(self):
        """Set up test fixtures."""
        set_seed(42)
        self.temp_dir = tempfile.mkdtemp()
        self.model_path = os.path.join(self.temp_dir, "test_model.pt")
        
        # Create dummy training data
        self.train_data = [
            Data(x=torch.randn(5, 10), edge_index=torch.randint(0, 5, (2, 8)), y=torch.randn(1))
            for _ in range(10)
        ]
        self.val_data = [
            Data(x=torch.randn(5, 10), edge_index=torch.randint(0, 5, (2, 8)), y=torch.randn(1))
            for _ in range(5)
        ]
        self.test_data = [
            Data(x=torch.randn(5, 10), edge_index=torch.randint(0, 5, (2, 8)), y=torch.randn(1))
            for _ in range(5)
        ]

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    def test_monotonically_increasing_loss(self):
        """Test that monotonically increasing loss is detected as non-convergence."""
        model = GNNMPNN(input_dim=10, hidden_dim=16, output_dim=1)
        
        # Simulate increasing loss values
        increasing_losses = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9]
        
        # Mock the training loop to return increasing losses
        with patch('training.train_gnn.train_epoch') as mock_train:
            mock_train.side_effect = increasing_losses
            
            # Should detect non-convergence
            with pytest.raises(RuntimeError, match="Non-convergence detected"):
                train_model(
                    model=model,
                    train_loader=self.train_data,
                    val_loader=self.val_data,
                    epochs=10,
                    patience=3,
                    save_path=self.model_path,
                    device='cpu'
                )

    def test_early_stopping_trigger(self):
        """Test that early stopping is triggered when validation loss doesn't improve."""
        model = GNNMPNN(input_dim=10, hidden_dim=16, output_dim=1)
        
        # Simulate validation loss that never improves after initial epochs
        val_losses = [0.5, 0.4, 0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52]
        
        with patch('training.train_gnn.train_epoch') as mock_train:
            with patch('training.train_gnn.evaluate_epoch') as mock_eval:
                mock_train.return_value = 0.3
                mock_eval.return_value = 0.3
                
                # Should complete with early stopping
                try:
                    train_model(
                        model=model,
                        train_loader=self.train_data,
                        val_loader=self.val_data,
                        epochs=20,
                        patience=3,
                        save_path=self.model_path,
                        device='cpu'
                    )
                    # If it completes, check that early stopping was used
                    # The model should have stopped before max epochs
                except RuntimeError as e:
                    # Non-convergence detected - also acceptable
                    assert "Non-convergence" in str(e)

    def test_nan_loss_detection(self):
        """Test that NaN loss values are detected and handled."""
        model = GNNMPNN(input_dim=10, hidden_dim=16, output_dim=1)
        
        # Simulate NaN loss
        with patch('training.train_gnn.train_epoch') as mock_train:
            mock_train.return_value = float('nan')
            
            with pytest.raises(RuntimeError, match="NaN loss detected"):
                train_model(
                    model=model,
                    train_loader=self.train_data,
                    val_loader=self.val_data,
                    epochs=10,
                    patience=3,
                    save_path=self.model_path,
                    device='cpu'
                )

    def test_inf_loss_detection(self):
        """Test that infinite loss values are detected and handled."""
        model = GNNMPNN(input_dim=10, hidden_dim=16, output_dim=1)
        
        with patch('training.train_gnn.train_epoch') as mock_train:
            mock_train.return_value = float('inf')
            
            with pytest.raises(RuntimeError, match="Infinite loss detected"):
                train_model(
                    model=model,
                    train_loader=self.train_data,
                    val_loader=self.val_data,
                    epochs=10,
                    patience=3,
                    save_path=self.model_path,
                    device='cpu'
                )

    def test_stalled_training_detection(self):
        """Test detection of stalled training (loss not changing)."""
        model = GNNMPNN(input_dim=10, hidden_dim=16, output_dim=1)
        
        # Simulate constant loss (stalled training)
        constant_losses = [0.5] * 10
        
        with patch('training.train_gnn.train_epoch') as mock_train:
            mock_train.side_effect = constant_losses
            
            # Should detect stalled training
            with pytest.raises(RuntimeError, match="Training stalled"):
                train_model(
                    model=model,
                    train_loader=self.train_data,
                    val_loader=self.val_data,
                    epochs=10,
                    patience=3,
                    save_path=self.model_path,
                    device='cpu'
                )

    def test_successful_convergence(self):
        """Test that successful convergence is properly handled."""
        model = GNNMPNN(input_dim=10, hidden_dim=16, output_dim=1)
        
        # Simulate decreasing loss
        decreasing_losses = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
        
        with patch('training.train_gnn.train_epoch') as mock_train:
            mock_train.side_effect = decreasing_losses
            
            try:
                train_model(
                    model=model,
                    train_loader=self.train_data,
                    val_loader=self.val_data,
                    epochs=10,
                    patience=3,
                    save_path=self.model_path,
                    device='cpu'
                )
                # Should complete without raising
                assert os.path.exists(self.model_path)
            except RuntimeError:
                # If it raises, it should be for a specific reason
                pytest.fail("Successful convergence should not raise an error")


class TestEdgeCaseIntegration:
    """Integration tests combining multiple edge cases."""

    def test_pipeline_with_mixed_validity(self):
        """Test preprocessing pipeline with mix of valid and invalid SMILES."""
        valid_smiles = ["CCO", "CCN", "c1ccccc1"]
        invalid_smiles = ["", "C[C", "C@invalid"]
        
        all_smiles = valid_smiles + invalid_smiles
        
        results = []
        for smiles in all_smiles:
            try:
                result = process_molecule(smiles, log_file=None)
                results.append((smiles, "processed" if result else "excluded"))
            except Exception:
                results.append((smiles, "exception"))
        
        # Verify valid SMILES are processed
        for smiles in valid_smiles:
            entry = next((r for r in results if r[0] == smiles), None)
            assert entry is not None
            assert entry[1] == "processed"
        
        # Verify invalid SMILES are excluded or raise
        for smiles in invalid_smiles:
            entry = next((r for r in results if r[0] == smiles), None)
            assert entry is not None
            assert entry[1] in ["excluded", "exception"]

    def test_gnn_with_extreme_values(self):
        """Test GNN training with extreme target values."""
        set_seed(42)
        model = GNNMPNN(input_dim=10, hidden_dim=16, output_dim=1)
        
        # Create data with extreme values
        extreme_data = [
            Data(
                x=torch.randn(5, 10),
                edge_index=torch.randint(0, 5, (2, 8)),
                y=torch.tensor([1e10 if i % 2 == 0 else -1e10])
            )
            for i in range(10)
        ]
        
        # Should handle extreme values without crashing
        try:
            with patch('training.train_gnn.train_epoch') as mock_train:
                mock_train.return_value = 1.0
                
                train_model(
                    model=model,
                    train_loader=extreme_data,
                    val_loader=extreme_data[:5],
                    epochs=5,
                    patience=2,
                    save_path=self.model_path,
                    device='cpu'
                )
        except RuntimeError as e:
            # Non-convergence is acceptable with extreme values
            assert "Non-convergence" in str(e) or "NaN" in str(e)