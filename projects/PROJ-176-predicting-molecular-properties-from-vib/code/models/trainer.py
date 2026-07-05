"""
Trainer module for MolecularPropertyCNN.
Implements CPU-only training with early stopping, Adam optimizer, and TensorBoard logging.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from torch.utils.tensorboard import SummaryWriter
from datetime import datetime

# Import project utilities
from models.cnn_1d import MolecularPropertyCNN
from utils.seed_utils import set_seed
from utils.timeout_wrapper import timeout_context, TimeoutError as ProjectTimeoutError

# Local import for stability check (re-implementing inline to avoid circular deps if stub is missing)
# Assuming check_tensor_stability exists or we implement a minimal version here if needed.
# Based on API surface: from models.trainer_stub import check_tensor_stability
try:
    from models.trainer_stub import check_tensor_stability, TrainingStabilityError
except ImportError:
    # Fallback if trainer_stub is not fully populated yet, though T025/T020 imply it exists
    class TrainingStabilityError(Exception):
        pass
    
    def check_tensor_stability(tensor: torch.Tensor) -> bool:
        """Check for NaN or Inf values."""
        return not (torch.isnan(tensor).any() or torch.isinf(tensor).any())

logger = logging.getLogger(__name__)

class Trainer:
    def __init__(
        self,
        model: MolecularPropertyCNN,
        device: str = "cpu",
        lr: float = 1e-3,
        patience: int = 10,
        log_dir: str = "runs/training",
        seed: int = 42,
        timeout_seconds: Optional[int] = None
    ):
        """
        Initialize the Trainer.
        
        Args:
            model: The MolecularPropertyCNN instance.
            device: Execution device (forced 'cpu').
            lr: Learning rate for Adam optimizer.
            patience: Early stopping patience (epochs).
            log_dir: Directory for TensorBoard logs.
            seed: Random seed for reproducibility.
            timeout_seconds: Optional timeout for the training run.
        """
        if device != "cpu":
            logger.warning("Device requested as non-CPU, but enforcing CPU-only execution as per constraints.")
        self.device = torch.device("cpu")
        self.model = model.to(self.device)
        self.patience = patience
        self.seed = seed
        self.timeout_seconds = timeout_seconds

        # Set seeds
        set_seed(seed)

        # Optimizer
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        
        # Loss function (MSE for regression)
        self.criterion = nn.MSELoss()

        # TensorBoard setup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.writer = SummaryWriter(log_dir=str(self.log_dir / timestamp))
        self.step_count = 0

        # State tracking
        self.best_val_loss = float('inf')
        self.patience_counter = 0
        self.training_history = {
            'train_loss': [],
            'val_loss': [],
            'best_val_loss': []
        }

    def _compute_weighted_loss(self, preds: Dict[str, torch.Tensor], targets: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Compute weighted sum of losses for the three heads.
        Weights are currently equal (1/3 each) but can be adjusted.
        """
        losses = []
        weights = [1.0, 1.0, 1.0] # dipole, polarizability, gap
        total_weight = sum(weights)

        for i, key in enumerate(['dipole', 'polarizability', 'homo_lumo_gap']):
            if key in preds and key in targets:
                loss = self.criterion(preds[key], targets[key])
                losses.append(loss * (weights[i] / total_weight))
        
        if not losses:
            return torch.tensor(0.0, device=self.device)
        
        return sum(losses)

    def train_epoch(self, dataloader: DataLoader) -> float:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch in dataloader:
            # Check for timeout
            if self.timeout_seconds:
                # Simple elapsed time check would require tracking start time outside loop
                # For strict enforcement, the caller should handle the timeout context
                pass

            spectra, targets = batch
            spectra = spectra.to(self.device)
            targets = {k: v.to(self.device) for k, v in targets.items()}

            self.optimizer.zero_grad()
            
            preds = self.model(spectra)
            
            # Stability check
            for k, v in preds.items():
                if not check_tensor_stability(v):
                    raise TrainingStabilityError(f"NaN/Inf detected in output head {k}")

            loss = self._compute_weighted_loss(preds, targets)
            
            if not check_tensor_stability(loss):
                raise TrainingStabilityError("NaN/Inf detected in loss")

            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1
            self.step_count += 1

            # Log to TensorBoard (every 100 steps to avoid clutter)
            if self.step_count % 100 == 0:
                self.writer.add_scalar('Loss/train_step', loss.item(), self.step_count)

        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        self.training_history['train_loss'].append(avg_loss)
        return avg_loss

    def validate(self, dataloader: DataLoader) -> Tuple[float, Dict[str, float]]:
        """Validate on the dataset."""
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        head_losses = {k: 0.0 for k in ['dipole', 'polarizability', 'homo_lumo_gap']}
        head_counts = {k: 0 for k in head_losses}

        with torch.no_grad():
            for batch in dataloader:
                spectra, targets = batch
                spectra = spectra.to(self.device)
                targets = {k: v.to(self.device) for k, v in targets.items()}

                preds = self.model(spectra)
                loss = self._compute_weighted_loss(preds, targets)

                total_loss += loss.item()
                num_batches += 1

                # Track individual head losses for reporting
                for k in head_losses:
                    if k in preds and k in targets:
                        head_losses[k] += self.criterion(preds[k], targets[k]).item()
                        head_counts[k] += 1

        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        avg_head_losses = {k: head_losses[k]/head_counts[k] if head_counts[k] > 0 else 0.0 for k in head_losses}

        self.training_history['val_loss'].append(avg_loss)
        self.training_history['best_val_loss'].append(self.best_val_loss if self.best_val_loss != float('inf') else avg_loss)

        return avg_loss, avg_head_losses

    def early_stop_check(self, val_loss: float) -> bool:
        """
        Check if training should stop early.
        Returns True if training should stop.
        """
        if val_loss < self.best_val_loss:
            self.best_val_loss = val_loss
            self.patience_counter = 0
            return False
        else:
            self.patience_counter += 1
            if self.patience_counter >= self.patience:
                logger.info(f"Early stopping triggered after patience ({self.patience}) exceeded.")
                return True
        return False

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 100
    ) -> Dict[str, Any]:
        """
        Full training loop.
        
        Returns:
            Dictionary containing final state and history.
        """
        logger.info(f"Starting training for {epochs} epochs on CPU.")
        logger.info(f"Early stopping patience: {self.patience}")

        start_time = datetime.now()

        # Use timeout context if specified
        if self.timeout_seconds:
            context_manager = timeout_context(self.timeout_seconds)
        else:
            # Dummy context if no timeout
            from contextlib import nullcontext
            context_manager = nullcontext()

        try:
            with context_manager:
                for epoch in range(epochs):
                    train_loss = self.train_epoch(train_loader)
                    val_loss, head_losses = self.validate(val_loader)

                    logger.info(f"Epoch {epoch+1}/{epochs} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}")
                    logger.info(f"  Head Losses: Dipole={head_losses['dipole']:.6f}, Pol={head_losses['polarizability']:.6f}, Gap={head_losses['homo_lumo_gap']:.6f}")

                    # Log to TensorBoard
                    self.writer.add_scalar('Loss/train_epoch', train_loss, epoch)
                    self.writer.add_scalar('Loss/val_epoch', val_loss, epoch)
                    for k, v in head_losses.items():
                        self.writer.add_scalar(f'Loss/head_{k}', v, epoch)

                    # Early stopping
                    if self.early_stop_check(val_loss):
                        logger.info(f"Stopping at epoch {epoch+1}")
                        break
        except ProjectTimeoutError:
            logger.warning("Training timed out. Saving current checkpoint.")
        except TrainingStabilityError as e:
            logger.error(f"Training stability error: {e}")
            raise

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        self.writer.close()

        return {
            'epochs_completed': epoch + 1,
            'total_duration_seconds': duration,
            'best_val_loss': self.best_val_loss,
            'history': self.training_history
        }

    def save_checkpoint(self, path: Path, epoch: int, is_best: bool = True):
        """Save model checkpoint."""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'best_val_loss': self.best_val_loss,
            'seed': self.seed
        }
        torch.save(checkpoint, path)
        logger.info(f"Checkpoint saved to {path}")

        if is_best:
            best_path = path.parent / "model_best.pt"
            torch.save(checkpoint, best_path)
            logger.info(f"New best model saved to {best_path}")

    def load_checkpoint(self, path: Path):
        """Load model checkpoint."""
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found at {path}")
        
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.best_val_loss = checkpoint.get('best_val_loss', float('inf'))
        logger.info(f"Loaded checkpoint from {path} (Epoch {checkpoint['epoch']})")

    def close(self):
        """Cleanup resources."""
        self.writer.close()


def main():
    """
    Example entry point for testing the trainer independently.
    Loads data from preprocessed .npz if available, or creates dummy data for testing.
    """
    import argparse
    import numpy as np

    parser = argparse.ArgumentParser(description="Train Molecular Property CNN")
    parser.add_argument("--data_path", type=str, default="data/preprocessed/aligned_data.npz", help="Path to preprocessed .npz file")
    parser.add_argument("--epochs", type=int, default=20, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Check if data exists, if not create dummy data for testing the trainer logic
    data_path = Path(args.data_path)
    if not data_path.exists():
        logger.warning(f"Data file {data_path} not found. Creating dummy data for trainer test.")
        # Create dummy data
        num_samples = 100
        spectrum_len = 400 # Approx 400-4000 cm-1 with 10 spacing
        spectra = torch.randn(num_samples, 1, spectrum_len)
        targets = {
            'dipole': torch.randn(num_samples, 1),
            'polarizability': torch.randn(num_samples, 1),
            'homo_lumo_gap': torch.randn(num_samples, 1)
        }
        dataset = TensorDataset(spectra, targets)
        train_loader = DataLoader(dataset, batch_size=16, shuffle=True)
        val_loader = DataLoader(dataset, batch_size=16, shuffle=False)
    else:
        # Load real data
        logger.info(f"Loading data from {data_path}")
        data = np.load(data_path)
        # Assuming keys: 'spectra', 'dipole', 'polarizability', 'homo_lumo_gap'
        # Adjust keys based on actual output of T014d
        spectra = torch.tensor(data['spectra']).float()
        if spectra.dim() == 2:
            spectra = spectra.unsqueeze(1) # Add channel dim
        
        targets = {
            'dipole': torch.tensor(data['dipole']).float(),
            'polarizability': torch.tensor(data['polarizability']).float(),
            'homo_lumo_gap': torch.tensor(data['homo_lumo_gap']).float()
        }
        
        # Simple split
        n = len(spectra)
        split_idx = int(0.8 * n)
        train_data = TensorDataset(spectra[:split_idx], {k: v[:split_idx] for k, v in targets.items()})
        val_data = TensorDataset(spectra[split_idx:], {k: v[split_idx:] for k, v in targets.items()})

        train_loader = DataLoader(train_data, batch_size=32, shuffle=True)
        val_loader = DataLoader(val_data, batch_size=32, shuffle=False)

    # Initialize Model
    model = MolecularPropertyCNN(input_dim=spectra.shape[-1])

    # Initialize Trainer
    trainer = Trainer(
        model=model,
        device="cpu",
        lr=args.lr,
        patience=args.patience,
        log_dir="runs/training",
        seed=args.seed
    )

    # Train
    try:
        results = trainer.train(train_loader, val_loader, epochs=args.epochs)
        trainer.save_checkpoint(Path("models/checkpoint.pt"), epoch=results['epochs_completed'])
        logger.info("Training completed successfully.")
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise
    finally:
        trainer.close()

if __name__ == "__main__":
    main()