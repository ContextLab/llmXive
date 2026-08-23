import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Tuple, Optional, Any, Dict

import numpy as np
import torch

# Import from existing API surface
from src.data.benchmarks import generate_polynomial_test_data
from src.models.baseline_transformer import create_baseline_transformer, BaselineTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExperimentConfig:
    seed: int = 42
    n_test_samples: int = 1000
    n_features: int = 10
    noise: float = 0.05
    model_path: Optional[str] = None
    output_dir: str = "data/results"

@dataclass
class ExperimentResult:
    config: Dict[str, Any]
    test_metrics: Dict[str, float]
    execution_time: float
    status: str
    details: Optional[str] = None

class BaselineRunner:
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.output_path = Path(config.output_dir)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Set seed for reproducibility
        np.random.seed(config.seed)
        torch.manual_seed(config.seed)
        
        self.X_test: Optional[np.ndarray] = None
        self.y_test: Optional[np.ndarray] = None
        self.model: Optional[BaselineTransformer] = None

    def load_test_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load test data from the generated polynomial dataset.
        T014a Implementation: Load `data/results/test_data_polynomial.npy`.
        
        Returns:
            Tuple of (X_test, y_test)
        
        Raises:
            FileNotFoundError: If the test data file does not exist.
            ValueError: If the file format is invalid.
        """
        # T008c generates this file. It must exist.
        # We do NOT fall back to synthetic generation. If it's missing, 
        # the pipeline is broken and must fail loudly.
        data_file = Path("data/results/test_data_polynomial.npy")
        
        if not data_file.exists():
            raise FileNotFoundError(
                f"Test data file not found at {data_file}. "
                "Please ensure T008c (generate_polynomial_test_data) has been executed successfully."
            )
        
        try:
            logger.info(f"Loading test data from {data_file}...")
            data = np.load(data_file, allow_pickle=True).item()
            
            if 'X' not in data or 'y' not in data:
                raise ValueError(f"Invalid data format in {data_file}. Expected keys 'X' and 'y'.")
            
            self.X_test = data['X']
            self.y_test = data['y']
            
            logger.info(f"Loaded test data: X shape {self.X_test.shape}, y shape {self.y_test.shape}")
            return self.X_test, self.y_test
            
        except Exception as e:
            logger.error(f"Failed to load test data: {e}")
            raise

    def load_model(self) -> BaselineTransformer:
        """Load the trained baseline model."""
        if self.config.model_path and os.path.exists(self.config.model_path):
            logger.info(f"Loading model from {self.config.model_path}")
            state_dict = torch.load(self.config.model_path, map_location='cpu')
            model = create_baseline_transformer()
            model.load_state_dict(state_dict)
            self.model = model
        else:
            logger.warning("No trained model found. Initializing random weights.")
            self.model = create_baseline_transformer()
        
        self.model.eval()
        return self.model

    def run_inference(self, X: np.ndarray) -> np.ndarray:
        """Run inference on input data."""
        if self.model is None:
            self.load_model()
        
        with torch.no_grad():
            # Convert numpy to torch tensor
            X_tensor = torch.FloatTensor(X)
            # Forward pass
            output = self.model(X_tensor)
            # Convert back to numpy
            y_pred = output.numpy()
        
        return y_pred

    def compute_generalization_mae(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Compute Mean Absolute Error."""
        return float(np.mean(np.abs(y_true - y_pred)))

    def write_generalization_report(self, mae: float, output_file: str = "generalization_report.md"):
        """Write the generalization report to disk."""
        report_path = self.output_path / output_file
        
        with open(report_path, 'w') as f:
            f.write("# Generalization Report\n\n")
            f.write(f"## Test Set Performance\n\n")
            f.write(f"- **Mean Absolute Error (MAE)**: {mae:.6f}\n")
            f.write(f"- **Test Samples**: {len(self.y_test)}\n")
            f.write(f"- **Features**: {self.X_test.shape[1]}\n\n")
            f.write(f"## Conclusion\n\n")
            if mae < 0.05:
                f.write("The model generalizes well to the polynomial test set (MAE < 0.05).\n")
            else:
                f.write(f"The model shows higher error on the polynomial test set (MAE = {mae:.6f}).\n")
        
        logger.info(f"Report written to {report_path}")

    def run_experiment(self) -> ExperimentResult:
        """Execute the full baseline validation pipeline."""
        start_time = time.time()
        
        try:
            # T014a: Load Test Data
            X_test, y_test = self.load_test_data()
            
            # T014b: Run Inference
            self.load_model()
            y_pred = self.run_inference(X_test)
            
            # T014c: Compute Metrics
            mae = self.compute_generalization_mae(y_test, y_pred)
            
            # T014d: Write Report
            self.write_generalization_report(mae)
            
            execution_time = time.time() - start_time
            
            return ExperimentResult(
                config=asdict(self.config),
                test_metrics={"mae": mae},
                execution_time=execution_time,
                status="success",
                details=f"MAE: {mae:.6f}"
            )
            
        except Exception as e:
            logger.error(f"Experiment failed: {e}")
            return ExperimentResult(
                config=asdict(self.config),
                test_metrics={},
                execution_time=time.time() - start_time,
                status="failed",
                details=str(e)
            )

def main():
    """CLI entry point for baseline runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run baseline transformer validation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--n-test-samples", type=int, default=1000, help="Number of test samples")
    parser.add_argument("--n-features", type=int, default=10, help="Number of input features")
    parser.add_argument("--noise", type=float, default=0.05, help="Noise level")
    parser.add_argument("--model-path", type=str, default=None, help="Path to trained model")
    parser.add_argument("--output-dir", type=str, default="data/results", help="Output directory")
    
    args = parser.parse_args()
    
    config = ExperimentConfig(
        seed=args.seed,
        n_test_samples=args.n_test_samples,
        n_features=args.n_features,
        noise=args.noise,
        model_path=args.model_path,
        output_dir=args.output_dir
    )
    
    runner = BaselineRunner(config)
    result = runner.run_experiment()
    
    print(json.dumps(asdict(result), indent=2))
    
    if result.status == "failed":
        sys.exit(1)

if __name__ == "__main__":
    main()