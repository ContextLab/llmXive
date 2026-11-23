"""
Training configuration for the Lightweight GNN.

Defines hyperparameters, early stopping patience, and CPU constraints.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import os


@dataclass
class TrainingConfig:
    """Configuration for GNN training."""

    # Model Architecture
    hidden_dim: int = 64
    num_layers: int = 3
    dropout: float = 0.1

    # Training Hyperparameters
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001
    weight_decay: float = 1e-5

    # Early Stopping
    early_stopping_patience: int = 10
    early_stopping_threshold: float = 1e-4

    # CPU Constraints
    max_memory_gb: float = 7.0
    cpu_only: bool = True
    num_workers: int = 0  # 0 for single-threaded to avoid overhead in restricted envs

    # Paths
    data_path: Optional[str] = None
    split_path: Optional[str] = None
    output_model_path: str = "data/processed/model_v1.pt"
    output_log_path: str = "data/results/training_logs.json"

    # Metadata
    disclaimer: str = (
        "These results are ML interpolations of DFT data, not first-principles solutions."
    )

    def __post_init__(self):
        """Validate configuration and apply environment overrides."""
        if self.cpu_only:
            os.environ["CUDA_VISIBLE_DEVICES"] = ""

        # Allow environment overrides for key parameters
        if os.getenv("TRAIN_EPOCHS"):
            self.epochs = int(os.getenv("TRAIN_EPOCHS"))
        if os.getenv("TRAIN_BATCH_SIZE"):
            self.batch_size = int(os.getenv("TRAIN_BATCH_SIZE"))
        if os.getenv("TRAIN_LR"):
            self.learning_rate = float(os.getenv("TRAIN_LR"))
        if os.getenv("TRAIN_HIDDEN_DIM"):
            self.hidden_dim = int(os.getenv("TRAIN_HIDDEN_DIM"))

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary for logging."""
        return {
            "hidden_dim": self.hidden_dim,
            "num_layers": self.num_layers,
            "dropout": self.dropout,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "early_stopping_patience": self.early_stopping_patience,
            "early_stopping_threshold": self.early_stopping_threshold,
            "max_memory_gb": self.max_memory_gb,
            "cpu_only": self.cpu_only,
            "num_workers": self.num_workers,
            "data_path": self.data_path,
            "split_path": self.split_path,
            "output_model_path": self.output_model_path,
            "output_log_path": self.output_log_path,
            "disclaimer": self.disclaimer,
        }


def load_config_from_args(args: Any) -> TrainingConfig:
    """
    Load configuration from argparse namespace, with defaults from TrainingConfig.

    Args:
        args: Parsed command line arguments.

    Returns:
        TrainingConfig instance.
    """
    config = TrainingConfig()

    # Override with CLI args if provided
    if hasattr(args, 'config') and args.config:
        # If a config file is provided, load from there (future implementation)
        # For now, we rely on CLI overrides or defaults
        pass

    if hasattr(args, 'epochs') and args.epochs is not None:
        config.epochs = args.epochs
    if hasattr(args, 'patience') and args.patience is not None:
        config.early_stopping_patience = args.patience
    if hasattr(args, 'batch_size') and args.batch_size is not None:
        config.batch_size = args.batch_size
    if hasattr(args, 'lr') and args.lr is not None:
        config.learning_rate = args.lr
    if hasattr(args, 'data_path') and args.data_path is not None:
        config.data_path = args.data_path
    if hasattr(args, 'split_path') and args.split_path is not None:
        config.split_path = args.split_path
    if hasattr(args, 'output_log') and args.output_log is not None:
        config.output_log_path = args.output_log
    if hasattr(args, 'output_model') and args.output_model is not None:
        config.output_model_path = args.output_model

    return config
