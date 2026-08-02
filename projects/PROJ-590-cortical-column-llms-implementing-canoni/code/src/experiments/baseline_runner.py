import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
import torch
import numpy as np

# Import existing API surface components
from src.models.baseline_transformer import BaselineTransformer, create_baseline_model
from src.data.benchmarks import generate_training_data, generate_test_data
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.training.homeostasis import log_gradient_norms

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ExperimentConfig:
    """Configuration for a baseline experiment."""
    model_name: str = "baseline_transformer"
    hidden_dim: int = 64
    num_layers: int = 4
    num_heads: int = 4
    max_seq_len: int = 128
    train_epochs: int = 50
    batch_size: int = 32
    learning_rate: float = 1e-4
    weight_decay: float = 1e-5
    seed: int = 42
    device: str = "cpu"
    log_gradients: bool = True
    gradient_log_path: str = "data/logs/gradient_norms.json"

@dataclass
class ExperimentResult:
    """Result container for a baseline experiment."""
    train_mae: float = 0.0
    test_mae: float = 0.0
    degradation_pct: float = 0.0
    training_time: float = 0.0
    total_params: int = 0
    passed: bool = False
    config: Optional[Dict[str, Any]] = None
    status: str = "unknown"

class BaselineRunner:
    """Manages the execution and recording of baseline experiments."""

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.device = torch.device(config.device)
        logger.info(f"Initialized BaselineRunner with device: {self.device}")

    def _setup_seed(self):
        """Set random seeds for reproducibility."""
        torch.manual_seed(self.config.seed)
        np.random.seed(self.config.seed)
        if self.config.device == "cuda":
            torch.cuda.manual_seed_all(self.config.seed)
        logger.info(f"Seeds set to {self.config.seed}")

    def _generate_data(self):
        """Generate training and test datasets."""
        logger.info("Generating training data (Lorenz)...")
        train_data = generate_training_data(seed=self.config.seed)
        logger.info("Generating test data (Polynomials)...")
        test_data = generate_test_data(seed=self.config.seed + 1) # Different seed for independence
        return train_data, test_data

    def _create_model(self):
        """Instantiate the baseline model."""
        logger.info(f"Creating model: {self.config.model_name}")
        model = create_baseline_model(
            hidden_dim=self.config.hidden_dim,
            num_layers=self.config.num_layers,
            num_heads=self.config.num_heads,
            max_seq_len=self.config.max_seq_len,
            device=self.device
        )
        total_params = sum(p.numel() for p in model.parameters())
        logger.info(f"Model created with {total_params:,} parameters")
        return model, total_params

    def run_and_record_metrics(self, output_path: str = "data/results/baseline_metrics.json") -> ExperimentResult:
        """
        Execute the baseline training and evaluation pipeline, calculating metrics
        and storing the result in a JSON file.

        Logic:
        1. Generate Train (Lorenz) and Test (Polynomials) data.
        2. Train model on Train data.
        3. Evaluate on Train and Test data to get MAE.
        4. Calculate degradation_pct.
        5. Determine 'passed' status (degradation < 10%).
        6. Write JSON to output_path.
        """
        self._setup_seed()
        start_time = time.time()
        
        try:
            # 1. Data Generation
            train_data, test_data = self._generate_data()
            if train_data is None or test_data is None:
                raise RuntimeError("Data generation failed.")

            # 2. Model Creation
            model, total_params = self._create_model()
            model = model.to(self.device)

            # 3. Training Configuration
            training_config = TrainingConfig(
                epochs=self.config.train_epochs,
                batch_size=self.config.batch_size,
                lr=self.config.learning_rate,
                weight_decay=self.config.weight_decay,
                device=self.device,
                log_gradients=self.config.log_gradients,
                gradient_log_path=self.config.gradient_log_path
            )

            # 4. Run Training
            logger.info("Starting training loop...")
            # run_training expects model, train_data, test_data (for eval), and config
            # It returns a dict with final metrics
            final_metrics = run_training(
                model=model,
                train_data=train_data,
                test_data=test_data,
                config=training_config
            )

            # Extract MAEs (assuming run_training returns these keys or we calculate them)
            # If run_training doesn't return them directly, we re-evaluate
            # Based on T012, run_training likely returns a dict with 'final_train_mae', 'final_test_mae'
            # We will assume standard return structure or calculate if missing.
            
            # Safely extract or calculate MAE
            train_mae = final_metrics.get('final_train_mae')
            test_mae = final_metrics.get('final_test_mae')

            if train_mae is None or test_mae is None:
                # Fallback: explicit evaluation if run_training didn't return them
                logger.warning("Metrics not in return dict, recalculating MAE explicitly...")
                model.eval()
                with torch.no_grad():
                    # Assuming train_data and test_data are tuples (X, y)
                    if isinstance(train_data, tuple) and len(train_data) == 2:
                        X_tr, y_tr = train_data
                        X_tr = torch.tensor(X_tr, dtype=torch.float32).to(self.device)
                        y_tr = torch.tensor(y_tr, dtype=torch.float32).to(self.device)
                        preds_tr = model(X_tr)
                        train_mae = calculate_mae(preds_tr, y_tr)
                    
                    if isinstance(test_data, tuple) and len(test_data) == 2:
                        X_te, y_te = test_data
                        X_te = torch.tensor(X_te, dtype=torch.float32).to(self.device)
                        y_te = torch.tensor(y_te, dtype=torch.float32).to(self.device)
                        preds_te = model(X_te)
                        test_mae = calculate_mae(preds_te, y_te)

            if train_mae is None or test_mae is None:
                raise RuntimeError("Failed to compute MAE for training or test sets.")

            # Round to 4 decimal places
            train_mae = round(float(train_mae), 4)
            test_mae = round(float(test_mae), 4)

            # Calculate degradation
            if train_mae > 0:
                degradation_pct = round(((test_mae - train_mae) / train_mae) * 100, 4)
            else:
                degradation_pct = 0.0

            # Determine pass status
            passed = degradation_pct < 10.0

            training_time = time.time() - start_time

            result = ExperimentResult(
                train_mae=train_mae,
                test_mae=test_mae,
                degradation_pct=degradation_pct,
                training_time=round(training_time, 2),
                total_params=total_params,
                passed=passed,
                config=asdict(self.config),
                status="completed" if passed else "failed_degradation"
            )

            # Write output
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(asdict(result), f, indent=2)
            
            logger.info(f"Metrics saved to {output_path}")
            logger.info(f"Train MAE: {train_mae}, Test MAE: {test_mae}, Degradation: {degradation_pct}%")
            logger.info(f"Status: {'PASSED' if passed else 'FAILED'}")

            return result

        except Exception as e:
            logger.error(f"Experiment failed: {e}", exc_info=True)
            training_time = time.time() - start_time
            result = ExperimentResult(
                train_mae=0.0,
                test_mae=0.0,
                degradation_pct=0.0,
                training_time=round(training_time, 2),
                total_params=0,
                passed=False,
                config=asdict(self.config),
                status=f"error: {str(e)}"
            )
            # Still write to file to record failure state as per requirements
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(asdict(result), f, indent=2)
            return result

def main():
    """Entry point for running the baseline experiment."""
    config = ExperimentConfig()
    runner = BaselineRunner(config)
    result = runner.run_and_record_metrics()
    
    # Exit with code 1 if failed, 0 if passed (for CI integration)
    sys.exit(0 if result.passed else 1)

if __name__ == "__main__":
    main()
