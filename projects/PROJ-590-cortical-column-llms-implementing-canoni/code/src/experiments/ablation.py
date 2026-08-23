import json
import os
import logging
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path

from src.models.microcircuit import MicrocircuitColumn, create_microcircuit_column, MicrocircuitColumnConfig
from src.models.hybrid_network import HybridNetwork, create_hybrid_network
from src.training.trainer import run_training, TrainingConfig
from src.data.benchmarks import generate_training_data, generate_polynomial_test_data
from src.experiments.baseline_runner import ExperimentConfig, ExperimentResult, BaselineRunner

logger = logging.getLogger(__name__)

@dataclass
class AblationConfig:
    name: str
    description: str
    disable_recurrence: bool = False
    disable_inhibition: bool = False
    disable_homeostasis: bool = False
    disable_laminar_topology: bool = False
    column_count: int = 1

@dataclass
class AblationResult:
    config_name: str
    description: str
    training_mae: float
    test_mae: float
    parameter_count: int
    training_time_sec: float
    success: bool
    error_message: Optional[str] = None

def generate_ablation_configs() -> List[AblationConfig]:
    """Generate a standard set of ablation configurations."""
    configs = [
        AblationConfig(
            name="full_model",
            description="Full microcircuit with all features",
            disable_recurrence=False,
            disable_inhibition=False,
            disable_homeostasis=False,
            disable_laminar_topology=False,
            column_count=1
        ),
        AblationConfig(
            name="no_recurrence",
            description="Without recurrent connections",
            disable_recurrence=True,
            disable_inhibition=False,
            disable_homeostasis=False,
            disable_laminar_topology=False,
            column_count=1
        ),
        AblationConfig(
            name="no_inhibition",
            description="Without inhibitory neurons",
            disable_recurrence=False,
            disable_inhibition=True,
            disable_homeostasis=False,
            disable_laminar_topology=False,
            column_count=1
        ),
        AblationConfig(
            name="no_homeostasis",
            description="Without homeostatic scaling",
            disable_recurrence=False,
            disable_inhibition=False,
            disable_homeostasis=True,
            disable_laminar_topology=False,
            column_count=1
        ),
        AblationConfig(
            name="no_laminar_topology",
            description="Without laminar connectivity constraints",
            disable_recurrence=False,
            disable_inhibition=False,
            disable_homeostasis=False,
            disable_laminar_topology=True,
            column_count=1
        ),
        AblationConfig(
            name="baseline_transformer",
            description="Standard Transformer baseline (no microcircuit)",
            disable_recurrence=False,
            disable_inhibition=False,
            disable_homeostasis=False,
            disable_laminar_topology=False,
            column_count=0  # Special flag for baseline
        )
    ]
    return configs

def save_ablation_configs(configs: List[AblationConfig], output_path: str):
    """Save ablation configs to a JSON file."""
    data = [asdict(c) for c in configs]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_ablation_configs(input_path: str) -> List[AblationConfig]:
    """Load ablation configs from a JSON file."""
    with open(input_path, 'r') as f:
        data = json.load(f)
    return [AblationConfig(**item) for item in data]

def create_ablated_microcircuit_column(config: AblationConfig) -> MicrocircuitColumn:
    """Create a microcircuit column with specified ablations."""
    base_config = MicrocircuitColumnConfig()
    
    # Apply ablations to the configuration
    if config.disable_laminar_topology:
        # Use a simplified connectivity (fully connected)
        base_config.use_laminar_topology = False
    
    # Create the column
    column = create_microcircuit_column(base_config)
    
    # For more complex ablations (recurrence, inhibition), we need to modify the module
    if config.disable_recurrence or config.disable_inhibition:
        # We'll handle this in the hybrid network creation by modifying the forward pass
        # or by creating a custom wrapper. For now, we note this in the config.
        column.ablation_flags = {
            'disable_recurrence': config.disable_recurrence,
            'disable_inhibition': config.disable_inhibition
        }
    
    return column

def create_ablated_hybrid_network(config: AblationConfig) -> nn.Module:
    """Create a hybrid network with specified ablations."""
    if config.column_count == 0:
        # Return standard baseline transformer
        from src.models.baseline_transformer import create_baseline_transformer
        return create_baseline_transformer()
    
    # Create microcircuit columns
    columns = []
    for _ in range(config.column_count):
        column = create_ablated_microcircuit_column(config)
        columns.append(column)
    
    # Create the hybrid network
    network = create_hybrid_network(
        num_columns=config.column_count,
        column_configs=[MicrocircuitColumnConfig() for _ in range(config.column_count)],
        ablation_flags={
            'disable_recurrence': config.disable_recurrence,
            'disable_inhibition': config.disable_inhibition,
            'disable_homeostasis': config.disable_homeostasis
        }
    )
    
    return network

def run_ablation_experiment(
    config: AblationConfig,
    train_data: np.ndarray,
    test_data: np.ndarray,
    training_config: Optional[TrainingConfig] = None
) -> AblationResult:
    """Run a single ablation experiment."""
    logger.info(f"Running ablation experiment: {config.name}")
    start_time = time.time()
    
    try:
        # Create model
        model = create_ablated_hybrid_network(config)
        param_count = sum(p.numel() for p in model.parameters())
        
        # Set up training config
        if training_config is None:
            training_config = TrainingConfig(
                epochs=10,
                batch_size=32,
                lr=0.001,
                device='cpu'
            )
        
        # Train model
        training_result = run_training(
            model=model,
            train_data=train_data,
            val_data=test_data,
            config=training_config
        )
        
        training_time = time.time() - start_time
        
        return AblationResult(
            config_name=config.name,
            description=config.description,
            training_mae=training_result.train_mae,
            test_mae=training_result.val_mae,
            parameter_count=param_count,
            training_time_sec=training_time,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Experiment {config.name} failed: {str(e)}")
        return AblationResult(
            config_name=config.name,
            description=config.description,
            training_mae=float('nan'),
            test_mae=float('nan'),
            parameter_count=0,
            training_time_sec=time.time() - start_time,
            success=False,
            error_message=str(e)
        )

def run_ablation_study(
    configs: Optional[List[AblationConfig]] = None,
    output_dir: str = "data/results",
    training_config: Optional[TrainingConfig] = None
) -> List[AblationResult]:
    """Run a full ablation study with multiple configurations."""
    if configs is None:
        configs = generate_ablation_configs()
    
    # Generate training and test data
    logger.info("Generating training data (Lorenz attractor)...")
    train_data = generate_training_data(n_samples=1000, seed=42)
    
    logger.info("Generating test data (polynomial surfaces)...")
    test_data = generate_polynomial_test_data(n_samples=200, seed=123)
    
    results = []
    for config in configs:
        result = run_ablation_experiment(config, train_data, test_data, training_config)
        results.append(result)
        logger.info(f"Completed {config.name}: MAE={result.test_mae:.4f}, Params={result.parameter_count}")
    
    # Save results
    output_path = os.path.join(output_dir, "ablation_results.json")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    results_data = [asdict(r) for r in results]
    with open(output_path, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    logger.info(f"Ablation study complete. Results saved to {output_path}")
    return results

def main():
    """Main entry point for running ablation study."""
    logging.basicConfig(level=logging.INFO)
    
    # Run the study
    results = run_ablation_study()
    
    # Print summary
    print("\nAblation Study Summary:")
    print("-" * 80)
    for r in results:
        status = "✓" if r.success else "✗"
        print(f"{status} {r.config_name:20s} | MAE: {r.test_mae:.4f} | Params: {r.parameter_count:,}")
    
    return results

if __name__ == "__main__":
    main()