import torch
import torch.nn as nn
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
import logging
import os
import json
import time
import sys

# Add project root to path for imports if running as script
if os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.models.microcircuit import MicrocircuitColumn, create_microcircuit_column
from src.models.hybrid_network import HybridNetwork, create_hybrid_network
from src.training.trainer import run_training, TrainingConfig, TrainingMetrics
from src.training.homeostasis import HomeostaticScaler, HomeostasisConfig
from src.data.benchmarks import generate_synthetic_dataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AblationConfig:
    """Configuration for a specific ablation variant."""
    name: str
    description: str
    remove_recurrence: bool = False
    remove_inhibition: bool = False
    remove_homeostasis: bool = False
    # Base parameters
    hidden_dim: int = 64
    neurons_per_layer: int = 128
    num_columns: int = 1
    num_layers: int = 4
    num_heads: int = 4
    seq_len: int = 128
    batch_size: int = 32
    epochs: int = 5
    learning_rate: float = 1e-3
    seed: int = 42

@dataclass
class AblationResult:
    """Result from a single ablation experiment."""
    config_name: str
    config_description: str
    train_mae: float
    test_mae: float
    degradation_pct: float
    training_time_sec: float
    peak_memory_mb: float
    params_count: int
    success: bool
    error_message: Optional[str] = None

def create_ablated_microcircuit_column(config: AblationConfig) -> MicrocircuitColumn:
    """
    Create a MicrocircuitColumn with specific ablations applied.
    Note: True ablation of recurrence/inhibition requires modifying the
    internal layer logic. For this implementation, we simulate ablation
    by modifying connectivity masks or disabling specific operations.
    """
    # We create a standard column first
    column = create_microcircuit_column(
        hidden_dim=config.hidden_dim,
        neurons_per_layer=config.neurons_per_layer,
        num_layers=config.num_layers,
        seed=config.seed
    )

    # Apply ablations
    if config.remove_recurrence:
        # Disable recurrence by zeroing recurrent weights in the layers
        # This is a simplified approach; in a real implementation,
        # we would have a flag in the layer config.
        logger.info(f"Ablating recurrence in {config.name}")
        for module in column.modules():
            if hasattr(module, 'recurrent_weight') and module.recurrent_weight is not None:
                module.recurrent_weight.data.zero_()

    if config.remove_inhibition:
        # Disable inhibition by setting inhibitory weights to zero
        logger.info(f"Ablating inhibition in {config.name}")
        for module in column.modules():
            if hasattr(module, 'inhibitory_weight') and module.inhibitory_weight is not None:
                module.inhibitory_weight.data.zero_()

    return column

def create_ablated_hybrid_network(config: AblationConfig) -> HybridNetwork:
    """
    Create a HybridNetwork with specific ablations applied.
    """
    network = create_hybrid_network(
        hidden_dim=config.hidden_dim,
        num_columns=config.num_columns,
        num_layers=config.num_layers,
        num_heads=config.num_heads,
        seq_len=config.seq_len,
        seed=config.seed
    )

    # Apply ablations to the underlying microcircuit columns
    if config.remove_recurrence or config.remove_inhibition:
        for col in network.columns:
            # Re-create or modify the column with ablations
            # For simplicity, we assume the column is a MicrocircuitColumn
            if isinstance(col, MicrocircuitColumn):
                # We need to re-create the column with the ablation flags
                # Since we can't easily pass flags to create_microcircuit_column,
                # we modify the existing one.
                for module in col.modules():
                    if hasattr(module, 'recurrent_weight') and config.remove_recurrence and module.recurrent_weight is not None:
                        module.recurrent_weight.data.zero_()
                    if hasattr(module, 'inhibitory_weight') and config.remove_inhibition and module.inhibitory_weight is not None:
                        module.inhibitory_weight.data.zero_()

    return network

def run_ablation_experiment(config: AblationConfig) -> AblationResult:
    """
    Run a single ablation experiment.
    """
    logger.info(f"Starting ablation experiment: {config.name}")
    start_time = time.time()

    try:
        # Create model
        model = create_ablated_hybrid_network(config)

        # Prepare data
        train_data, test_data = generate_synthetic_dataset(
            task='lorenz',
            seq_len=config.seq_len,
            batch_size=config.batch_size,
            train_size=1000,
            test_size=200,
            seed=config.seed
        )

        # Training config
        train_config = TrainingConfig(
            epochs=config.epochs,
            learning_rate=config.learning_rate,
            batch_size=config.batch_size,
            seed=config.seed,
            log_interval=10,
            homeostasis_config=HomeostasisConfig(
                enabled=not config.remove_homeostasis,
                target_ratio=4.0,
                decay_rate=0.1
            )
        )

        # Run training
        metrics: TrainingMetrics = run_training(
            model=model,
            train_loader=train_data,
            test_loader=test_data,
            config=train_config
        )

        end_time = time.time()
        training_time = end_time - start_time

        # Calculate degradation
        degradation = ((metrics.test_mae - metrics.train_mae) / metrics.train_mae * 100) if metrics.train_mae > 0 else 0.0

        # Count parameters
        params_count = sum(p.numel() for p in model.parameters() if p.requires_grad)

        return AblationResult(
            config_name=config.name,
            config_description=config.description,
            train_mae=metrics.train_mae,
            test_mae=metrics.test_mae,
            degradation_pct=degradation,
            training_time_sec=training_time,
            peak_memory_mb=metrics.peak_memory_mb,
            params_count=params_count,
            success=True
        )

    except Exception as e:
        logger.error(f"Experiment {config.name} failed: {str(e)}", exc_info=True)
        return AblationResult(
            config_name=config.name,
            config_description=config.description,
            train_mae=0.0,
            test_mae=0.0,
            degradation_pct=0.0,
            training_time_sec=0.0,
            peak_memory_mb=0.0,
            params_count=0,
            success=False,
            error_message=str(e)
        )

def generate_ablation_configs() -> List[AblationConfig]:
    """
    Generate configuration objects for four variants:
    - full: No ablations
    - no_recurrence: Recurrence disabled
    - no_inhibition: Inhibition disabled
    - no_homeostasis: Homeostatic scaling disabled
    """
    base_config = AblationConfig(
        name="base",
        description="Base configuration",
        hidden_dim=64,
        neurons_per_layer=128,
        num_columns=1,
        num_layers=4,
        num_heads=4,
        seq_len=128,
        batch_size=32,
        epochs=5,
        learning_rate=1e-3,
        seed=42
    )

    configs = [
        AblationConfig(
            name="full",
            description="Full microcircuit with all features",
            hidden_dim=base_config.hidden_dim,
            neurons_per_layer=base_config.neurons_per_layer,
            num_columns=base_config.num_columns,
            num_layers=base_config.num_layers,
            num_heads=base_config.num_heads,
            seq_len=base_config.seq_len,
            batch_size=base_config.batch_size,
            epochs=base_config.epochs,
            learning_rate=base_config.learning_rate,
            seed=base_config.seed,
            remove_recurrence=False,
            remove_inhibition=False,
            remove_homeostasis=False
        ),
        AblationConfig(
            name="no_recurrence",
            description="Microcircuit without recurrence",
            hidden_dim=base_config.hidden_dim,
            neurons_per_layer=base_config.neurons_per_layer,
            num_columns=base_config.num_columns,
            num_layers=base_config.num_layers,
            num_heads=base_config.num_heads,
            seq_len=base_config.seq_len,
            batch_size=base_config.batch_size,
            epochs=base_config.epochs,
            learning_rate=base_config.learning_rate,
            seed=base_config.seed,
            remove_recurrence=True,
            remove_inhibition=False,
            remove_homeostasis=False
        ),
        AblationConfig(
            name="no_inhibition",
            description="Microcircuit without inhibition",
            hidden_dim=base_config.hidden_dim,
            neurons_per_layer=base_config.neurons_per_layer,
            num_columns=base_config.num_columns,
            num_layers=base_config.num_layers,
            num_heads=base_config.num_heads,
            seq_len=base_config.seq_len,
            batch_size=base_config.batch_size,
            epochs=base_config.epochs,
            learning_rate=base_config.learning_rate,
            seed=base_config.seed,
            remove_recurrence=False,
            remove_inhibition=True,
            remove_homeostasis=False
        ),
        AblationConfig(
            name="no_homeostasis",
            description="Microcircuit without homeostatic scaling",
            hidden_dim=base_config.hidden_dim,
            neurons_per_layer=base_config.neurons_per_layer,
            num_columns=base_config.num_columns,
            num_layers=base_config.num_layers,
            num_heads=base_config.num_heads,
            seq_len=base_config.seq_len,
            batch_size=base_config.batch_size,
            epochs=base_config.epochs,
            learning_rate=base_config.learning_rate,
            seed=base_config.seed,
            remove_recurrence=False,
            remove_inhibition=False,
            remove_homeostasis=True
        )
    ]

    return configs

def run_ablation_study(output_path: str = "data/results/ablation_results.json") -> Dict[str, Any]:
    """
    Orchestrate training of ALL FOUR variants defined in generate_ablation_configs
    and aggregate results into a JSON file.
    """
    logger.info("Starting ablation study")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Generate configs
    configs = generate_ablation_configs()

    # Save configs for reference
    configs_path = "data/configs/ablation_configs.json"
    os.makedirs(os.path.dirname(configs_path), exist_ok=True)
    with open(configs_path, 'w') as f:
        json.dump([asdict(c) for c in configs], f, indent=2)
    logger.info(f"Saved ablation configs to {configs_path}")

    results = []
    for config in configs:
        result = run_ablation_experiment(config)
        results.append(asdict(result))
        logger.info(f"Completed {config.name}: train_mae={result.train_mae:.4f}, test_mae={result.test_mae:.4f}")

    # Aggregate results
    summary = {
        "study_name": "Ablation Study",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_variants": len(results),
        "successful_variants": sum(1 for r in results if r['success']),
        "results": results
    }

    # Write output
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Ablation study completed. Results saved to {output_path}")
    return summary

def main():
    """Main entry point for the ablation study script."""
    import argparse

    parser = argparse.ArgumentParser(description="Run ablation study on microcircuit variants")
    parser.add_argument("--output", type=str, default="data/results/ablation_results.json",
                      help="Output path for results JSON")
    args = parser.parse_args()

    run_ablation_study(args.output)

if __name__ == "__main__":
    main()