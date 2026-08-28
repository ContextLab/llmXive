import json
import logging
import os
import sys
import time
import numpy as np
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# Ensure we can import from src if running as script or module
if __name__ == "__main__" and "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.benchmarks import load_data

logger = logging.getLogger(__name__)

@dataclass
class ExperimentConfig:
    seed: int = 42
    data_path: str = "data/results/test_data_polynomial.npy"
    model_path: str = "data/models/baseline.pt"
    output_path: str = "data/results/experiment_result.json"

@dataclass
class ExperimentResult:
    config: ExperimentConfig
    mae: float = 0.0
    rmse: float = 0.0
    inference_time_sec: float = 0.0
    n_samples: int = 0
    success: bool = False
    error: Optional[str] = None

class BaselineRunner:
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.X_test: Optional[np.ndarray] = None
        self.y_test: Optional[np.ndarray] = None
        self.y_pred: Optional[np.ndarray] = None
        self.model = None

    def load_test_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load test data from the specified file path.
        
        This implements T014a: Load Test Data.
        
        Returns:
            Tuple of (X_test, y_test)
        
        Raises:
            FileNotFoundError: If the data file does not exist.
            ValueError: If the data format is invalid.
        """
        data_path = Path(self.config.data_path)
        
        if not data_path.exists():
            raise FileNotFoundError(
                f"Test data file not found at: {data_path}. "
                f"Ensure T008c (generate_polynomial_test_data) has been executed."
            )
        
        logger.info(f"Loading test data from: {data_path}")
        
        try:
            # load_data returns a dict with 'X' and 'y' keys based on benchmarks.py
            data_dict = load_data(str(data_path))
            
            if not isinstance(data_dict, dict):
                raise ValueError(f"Expected dict from load_data, got {type(data_dict)}")
            
            if 'X' not in data_dict or 'y' not in data_dict:
                raise ValueError(f"Data dict missing 'X' or 'y' keys: {data_dict.keys()}")
            
            X_test = data_dict['X']
            y_test = data_dict['y']
            
            # Ensure proper types
            if not isinstance(X_test, np.ndarray):
                X_test = np.array(X_test)
            if not isinstance(y_test, np.ndarray):
                y_test = np.array(y_test)
            
            logger.info(f"Loaded test data: X shape={X_test.shape}, y shape={y_test.shape}")
            
            self.X_test = X_test
            self.y_test = y_test
            
            return X_test, y_test
            
        except Exception as e:
            logger.error(f"Failed to load test data: {e}")
            raise

    def run_inference(self) -> np.ndarray:
        """Run inference on loaded test data."""
        if self.X_test is None or self.y_test is None:
            raise RuntimeError("Test data not loaded. Call load_test_data first.")
        
        if self.model is None:
            raise RuntimeError("Model not loaded.")
        
        logger.info("Running inference...")
        start_time = time.time()
        
        # Ensure model is in eval mode
        self.model.eval()
        
        # Move data to device if needed (assuming CPU for this task)
        with torch.no_grad():
            # Convert numpy to torch tensors if necessary
            X_tensor = torch.FloatTensor(self.X_test)
            y_pred_tensor = self.model(X_tensor)
            self.y_pred = y_pred_tensor.numpy()
        
        self.inference_time_sec = time.time() - start_time
        logger.info(f"Inference completed in {self.inference_time_sec:.4f}s")
        
        return self.y_pred

    def compute_generalization_mae(self) -> float:
        """Compute MAE between predictions and true values."""
        if self.y_pred is None or self.y_test is None:
            raise RuntimeError("Cannot compute MAE. Ensure inference has been run.")
        
        mae = np.mean(np.abs(self.y_test - self.y_pred))
        logger.info(f"Generalization MAE: {mae:.6f}")
        return mae

    def write_generalization_report(self, mae: float, output_file: Optional[str] = None) -> str:
        """Write generalization report to markdown file."""
        if output_file is None:
            output_file = self.config.output_path.replace('.json', '.md')
        
        report_path = Path(output_file)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write("# Generalization Report\n\n")
            f.write(f"**Test Data**: {self.config.data_path}\n\n")
            f.write(f"**Model**: {self.config.model_path}\n\n")
            f.write(f"**MAE**: {mae:.6f}\n\n")
            f.write(f"**Inference Time**: {self.inference_time_sec:.4f}s\n\n")
            f.write(f"**Samples**: {len(self.y_test)}\n\n")
            f.write("## Conclusion\n\n")
            f.write(f"The baseline model achieved a MAE of {mae:.6f} on the polynomial test set.\n")
        
        logger.info(f"Report written to: {report_path}")
        return str(report_path)

    def run_experiment(self) -> ExperimentResult:
        """Run the full experiment pipeline."""
        try:
            # Load test data
            X_test, y_test = self.load_test_data()
            
            # Load model (placeholder for T011a_run)
            # This assumes the model is saved as a torch state dict or full model
            import torch
            import torch.nn as nn
            from src.models.baseline_transformer import BaselineTransformer
            
            self.model = BaselineTransformer()
            if os.path.exists(self.config.model_path):
                state_dict = torch.load(self.config.model_path, map_location='cpu')
                self.model.load_state_dict(state_dict)
            else:
                raise FileNotFoundError(f"Model file not found: {self.config.model_path}")
            
            # Run inference
            y_pred = self.run_inference()
            
            # Compute metrics
            mae = self.compute_generalization_mae()
            rmse = np.sqrt(np.mean((self.y_test - y_pred) ** 2))
            
            # Write report
            self.write_generalization_report(mae)
            
            return ExperimentResult(
                config=self.config,
                mae=mae,
                rmse=rmse,
                inference_time_sec=self.inference_time_sec,
                n_samples=len(y_test),
                success=True
            )
            
        except Exception as e:
            logger.exception("Experiment failed")
            return ExperimentResult(
                config=self.config,
                success=False,
                error=str(e)
            )

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run baseline experiment")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--data", type=str, default="data/results/test_data_polynomial.npy")
    parser.add_argument("--model", type=str, default="data/models/baseline.pt")
    parser.add_argument("--output", type=str, default="data/results/experiment_result.json")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    config = ExperimentConfig(
        seed=args.seed,
        data_path=args.data,
        model_path=args.model,
        output_path=args.output
    )
    
    runner = BaselineRunner(config)
    result = runner.run_experiment()
    
    # Save result as JSON
    with open(args.output, 'w') as f:
        json.dump(asdict(result), f, indent=2)
    
    if result.success:
        print(f"Experiment successful. MAE: {result.mae:.6f}")
        sys.exit(0)
    else:
        print(f"Experiment failed: {result.error}")
        sys.exit(1)

if __name__ == "__main__":
    main()