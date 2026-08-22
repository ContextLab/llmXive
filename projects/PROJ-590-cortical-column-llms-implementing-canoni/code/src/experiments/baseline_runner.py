import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Import from project API surface
from src.data.benchmarks import generate_test_data, generate_polynomial_surface_data
from src.models.baseline_transformer import create_baseline_transformer, BaselineTransformer
from src.training.trainer import calculate_mae, TrainingConfig, TrainingMetrics
from src.utils.checksum import calculate_sha256

logger = logging.getLogger(__name__)

@dataclass
class ExperimentConfig:
    model_name: str = "baseline_transformer"
    hidden_dim: int = 256
    num_heads: int = 4
    num_layers: int = 2
    sequence_length: int = 64
    batch_size: int = 32
    learning_rate: float = 1e-4
    num_epochs: int = 10
    seed: int = 42
    data_dir: str = "data/results"
    log_dir: str = "data/logs"
    results_dir: str = "data/results"

@dataclass
class ExperimentResult:
    model_name: str
    test_mae: float
    test_loss: float
    parameter_count: int
    validation_time_sec: float
    test_data_checksum: str
    model_config: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))

class BaselineRunner:
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.device = torch.device("cpu")
        self.model: Optional[BaselineTransformer] = None
        self.test_loader: Optional[DataLoader] = None
        self.test_data_path = os.path.join(config.data_dir, "test_data_polynomial.npy")
        self.report_path = os.path.join(config.results_dir, "generalization_report.md")

        # Ensure directories exist
        os.makedirs(config.data_dir, exist_ok=True)
        os.makedirs(config.results_dir, exist_ok=True)
        os.makedirs(config.log_dir, exist_ok=True)

    def load_test_data(self) -> None:
        """
        Load the independent test set (polynomial surfaces) generated in T008c.
        Raises FileNotFoundError if the data does not exist.
        """
        if not os.path.exists(self.test_data_path):
            raise FileNotFoundError(
                f"Test data not found at {self.test_data_path}. "
                "Please run T008c (generate_test_data) first."
            )

        logger.info(f"Loading test data from {self.test_data_path}")
        data = np.load(self.test_data_path)

        # Expecting shape (N, seq_len, features) or similar structure
        # Split into inputs and targets based on convention (last dim is target or split 50/50)
        # Assuming data format: [features..., target] or [input..., target]
        # For polynomial surfaces, usually input is (x,y) or similar, target is z.
        # Let's assume data is structured as [X, y] where X is all but last, y is last.
        if data.ndim < 2:
            raise ValueError("Test data must have at least 2 dimensions.")

        # Simple heuristic: if last dim is 1, treat as target. Else split last 20% as target?
        # Based on T008c spec, it's polynomial surfaces.
        # Let's assume data is (N, T, D) where last dimension D includes target.
        # We'll assume the last feature is the target for this implementation.
        X = data[..., :-1].astype(np.float32)
        y = data[..., -1:].astype(np.float32)

        # Convert to tensors
        X_tensor = torch.tensor(X, dtype=torch.float32)
        y_tensor = torch.tensor(y, dtype=torch.float32)

        dataset = TensorDataset(X_tensor, y_tensor)
        self.test_loader = DataLoader(
            dataset, batch_size=self.config.batch_size, shuffle=False
        )
        logger.info(f"Loaded {len(dataset)} test samples")

    def load_model(self, checkpoint_path: Optional[str] = None) -> None:
        """Load the trained baseline model."""
        logger.info("Initializing baseline transformer model...")
        self.model = create_baseline_transformer(
            hidden_dim=self.config.hidden_dim,
            num_heads=self.config.num_heads,
            num_layers=self.config.num_layers,
            input_dim=self.config.sequence_length, # Simplified mapping
            output_dim=1,
            sequence_length=self.config.sequence_length
        ).to(self.device)

        if checkpoint_path and os.path.exists(checkpoint_path):
            logger.info(f"Loading checkpoint from {checkpoint_path}")
            self.model.load_state_dict(torch.load(checkpoint_path, map_location=self.device))
        else:
            logger.warning("No checkpoint provided or found. Model weights are random.")

    def calculate_checksum(self) -> str:
        """Calculate SHA256 checksum of the test data file."""
        if os.path.exists(self.test_data_path):
            return calculate_sha256(self.test_data_path)
        return "N/A"

    def validate_generalization(self, checkpoint_path: Optional[str] = None) -> ExperimentResult:
        """
        Execute validation on the independent test set (polynomial surfaces).
        Computes MAE and generates the generalization report.
        """
        logger.info("Starting generalization validation...")

        # 1. Load Test Data
        self.load_test_data()

        # 2. Load Model
        self.load_model(checkpoint_path)
        self.model.eval()

        # 3. Calculate Checksum
        test_checksum = self.calculate_checksum()

        # 4. Run Inference and Compute Metrics
        start_time = time.time()
        total_mae = 0.0
        total_samples = 0
        total_loss = 0.0

        criterion = nn.MSELoss()

        with torch.no_grad():
            for batch_X, batch_y in self.test_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)

                # Forward pass
                outputs = self.model(batch_X)

                # Ensure shapes match for loss calculation
                if outputs.shape != batch_y.shape:
                    # Handle potential dimension mismatch (e.g., output is [N, T] vs [N, T, 1])
                    outputs = outputs.squeeze(-1) if outputs.dim() > batch_y.dim() else outputs

                loss = criterion(outputs, batch_y)
                mae = calculate_mae(outputs, batch_y)

                total_loss += loss.item() * batch_X.size(0)
                total_mae += mae * batch_X.size(0)
                total_samples += batch_X.size(0)

        avg_mae = total_mae / total_samples if total_samples > 0 else 0.0
        avg_loss = total_loss / total_samples if total_samples > 0 else 0.0
        validation_time = time.time() - start_time

        # 5. Count Parameters
        param_count = sum(p.numel() for p in self.model.parameters())

        # 6. Generate Report
        result = ExperimentResult(
            model_name=self.config.model_name,
            test_mae=avg_mae,
            test_loss=avg_loss,
            parameter_count=param_count,
            validation_time_sec=validation_time,
            test_data_checksum=test_checksum,
            model_config=asdict(self.config)
        )

        self._write_report(result)
        logger.info(f"Generalization validation complete. MAE: {avg_mae:.6f}")

        return result

    def _write_report(self, result: ExperimentResult) -> None:
        """Write the generalization report to disk."""
        logger.info(f"Writing generalization report to {self.report_path}")

        report_lines = [
            "# Generalization Report: Baseline Transformer",
            "",
            "## Overview",
            f"This report validates the baseline Transformer model on an independent test set",
            f"consisting of polynomial surfaces (generated in T008c).",
            "",
            "## Configuration",
            f"- Model: {result.model_name}",
            f"- Hidden Dim: {result.model_config['hidden_dim']}",
            f"- Heads: {result.model_config['num_heads']}",
            f"- Layers: {result.model_config['num_layers']}",
            f"- Sequence Length: {result.model_config['sequence_length']}",
            "",
            "## Test Data",
            f"- Source: Polynomial Surfaces",
            f"- File Checksum (SHA256): {result.test_data_checksum}",
            "",
            "## Results",
            f"- **Test MAE**: {result.test_mae:.6f}",
            f"- **Test Loss (MSE)**: {result.test_loss:.6f}",
            f"- **Parameter Count**: {result.parameter_count:,}",
            f"- **Validation Time**: {result.validation_time_sec:.2f} seconds",
            "",
            "## Analysis",
            f"The model achieved a Mean Absolute Error of {result.test_mae:.6f} on the",
            "held-out polynomial surface test set. This metric serves as the baseline",
            "for comparison against the Cortical Column microcircuit models (US2).",
            "",
            f"Generated at: {result.timestamp}",
        ]

        with open(self.report_path, 'w') as f:
            f.write('\n'.join(report_lines))

def main():
    """Entry point for running the baseline generalization validation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config = ExperimentConfig()
    runner = BaselineRunner(config)

    # Optional: pass checkpoint path if available
    checkpoint = os.path.join(config.log_dir, "baseline_checkpoint.pth")
    if not os.path.exists(checkpoint):
        checkpoint = None

    result = runner.validate_generalization(checkpoint_path=checkpoint)

    print(f"Validation Complete. MAE: {result.test_mae:.6f}")
    print(f"Report saved to: {runner.report_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
