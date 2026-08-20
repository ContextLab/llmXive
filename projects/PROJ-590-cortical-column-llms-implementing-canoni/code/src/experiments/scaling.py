import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
import torch
import torch.nn as nn
import numpy as np
from scipy import stats

from src.models.microcircuit import create_microcircuit_column, MicrocircuitColumnConfig
from src.models.baseline_transformer import create_baseline_transformer, BaselineTransformer
from src.models.hybrid_network import create_hybrid_network, HybridNetwork
from src.training.trainer import TrainingConfig, run_training, TrainingMetrics
from src.training.homeostasis import HomeostasisConfig
from src.data.benchmarks import generate_training_data, generate_test_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScalingConfig:
    """Configuration for a single scaling experiment variant."""
    variant_name: str
    model_type: str  # 'microcircuit', 'baseline', 'hybrid'
    num_columns: int
    hidden_dim: int
    num_heads: int
    num_layers: int
    dropout: float = 0.1
    learning_rate: float = 1e-4
    batch_size: int = 32
    num_epochs: int = 10
    device: str = 'cpu'
    seed: int = 42

@dataclass
class ScalingResult:
    """Results from a single scaling experiment."""
    variant_name: str
    model_type: str
    num_columns: int
    total_parameters: int
    training_time_seconds: float
    metrics: Dict[str, float]
    config: Dict[str, Any]

def count_parameters(model: nn.Module) -> int:
    """Count total trainable parameters in a model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def create_model_from_config(config: ScalingConfig) -> nn.Module:
    """Create a model instance from a ScalingConfig."""
    if config.model_type == 'microcircuit':
        model_config = MicrocircuitColumnConfig(
            num_columns=config.num_columns,
            hidden_dim=config.hidden_dim,
            num_heads=config.num_heads,
            num_layers=config.num_layers,
            dropout=config.dropout
        )
        model = create_microcircuit_column(model_config)
    elif config.model_type == 'baseline':
        model = create_baseline_transformer(
            d_model=config.hidden_dim,
            nhead=config.num_heads,
            num_layers=config.num_layers,
            dim_feedforward=config.hidden_dim * 4,
            dropout=config.dropout
        )
    elif config.model_type == 'hybrid':
        model = create_hybrid_network(
            d_model=config.hidden_dim,
            nhead=config.num_heads,
            num_layers=config.num_layers,
            num_columns=config.num_columns,
            dropout=config.dropout
        )
    else:
        raise ValueError(f"Unknown model_type: {config.model_type}")
    
    return model

def train_scaling_variant(
    config: ScalingConfig,
    output_dir: str
) -> ScalingResult:
    """Train a single scaling variant and return results."""
    logger.info(f"Training variant: {config.variant_name}")
    
    # Set seed for reproducibility
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)
    
    # Create model
    model = create_model_from_config(config)
    total_params = count_parameters(model)
    logger.info(f"Model {config.variant_name} has {total_params:,} parameters")
    
    # Generate data
    train_data = generate_training_data(seed=config.seed)
    test_data = generate_test_data(seed=config.seed + 1000)
    
    # Configure training
    training_config = TrainingConfig(
        model_name=config.variant_name,
        learning_rate=config.learning_rate,
        batch_size=config.batch_size,
        num_epochs=config.num_epochs,
        device=config.device,
        gradient_clip_norm=1.0,
        homeostasis_config=HomeostasisConfig(
            enabled=True,
            target_ei_ratio=4.0,
            decay_rate=0.01
        )
    )
    
    # Train
    start_time = time.time()
    metrics = run_training(
        model=model,
        train_data=train_data,
        test_data=test_data,
        config=training_config,
        output_dir=output_dir
    )
    training_time = time.time() - start_time
    
    logger.info(f"Training completed in {training_time:.2f}s")
    logger.info(f"Final MAE: {metrics['test_mae']:.4f}")
    
    return ScalingResult(
        variant_name=config.variant_name,
        model_type=config.model_type,
        num_columns=config.num_columns,
        total_parameters=total_params,
        training_time_seconds=training_time,
        metrics=metrics,
        config=asdict(config)
    )

def create_scaling_configs(
    base_config: ScalingConfig,
    num_columns_range: List[int],
    hidden_dim_range: List[int],
    num_layers_range: List[int],
    model_types: List[str]
) -> List[ScalingConfig]:
    """Generate a grid of scaling configurations."""
    configs = []
    idx = 0
    
    for model_type in model_types:
        for num_cols in num_columns_range:
            for hidden_dim in hidden_dim_range:
                for num_layers in num_layers_range:
                    variant_name = f"{model_type}_c{num_cols}_h{hidden_dim}_l{num_layers}"
                    config = ScalingConfig(
                        variant_name=variant_name,
                        model_type=model_type,
                        num_columns=num_cols,
                        hidden_dim=hidden_dim,
                        num_heads=base_config.num_heads,
                        num_layers=num_layers,
                        dropout=base_config.dropout,
                        learning_rate=base_config.learning_rate,
                        batch_size=base_config.batch_size,
                        num_epochs=base_config.num_epochs,
                        device=base_config.device,
                        seed=base_config.seed
                    )
                    configs.append(config)
                    idx += 1
    
    logger.info(f"Generated {len(configs)} scaling configurations")
    return configs

def run_scaling_study(
    configs: List[ScalingConfig],
    output_dir: str
) -> List[ScalingResult]:
    """Run the full scaling study."""
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    for config in configs:
        try:
            result = train_scaling_variant(config, output_dir)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to train {config.variant_name}: {e}")
            continue
    
    return results

def save_scaling_results(results: List[ScalingResult], output_path: str):
    """Save scaling results to a JSON file."""
    data = [asdict(r) for r in results]
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(results)} results to {output_path}")

def calculate_scaling_exponent(
    results: List[ScalingResult],
    metric: str = 'test_mae'
) -> Tuple[float, float, float]:
    """
    Calculate the scaling exponent for a given metric.
    
    Fits a power law: metric = a * (parameters)^b
    Returns (exponent, intercept, r_squared)
    """
    parameters = np.array([r.total_parameters for r in results])
    values = np.array([r.metrics.get(metric, float('inf')) for r in results])
    
    # Filter out infinite values
    valid_mask = np.isfinite(values)
    parameters = parameters[valid_mask]
    values = values[valid_mask]
    
    if len(parameters) < 2:
        logger.warning("Not enough valid data points to calculate scaling exponent")
        return 0.0, 0.0, 0.0
    
    # Log-log fit
    log_params = np.log(parameters)
    log_values = np.log(values)
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_params, log_values)
    
    logger.info(f"Scaling exponent for {metric}: {slope:.4f} (R²={r_value**2:.4f})")
    return slope, intercept, r_value**2

def analyze_scaling_laws(
    results: List[ScalingResult],
    output_dir: str
):
    """Analyze scaling laws and generate summary statistics."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate scaling exponents for different metrics
    metrics_to_analyze = ['test_mae', 'training_time_seconds']
    scaling_analysis = {}
    
    for metric in metrics_to_analyze:
        exponent, intercept, r_squared = calculate_scaling_exponent(results, metric)
        scaling_analysis[metric] = {
            'exponent': exponent,
            'intercept': intercept,
            'r_squared': r_squared
        }
    
    # Save analysis
    analysis_path = os.path.join(output_dir, 'scaling_analysis.json')
    with open(analysis_path, 'w') as f:
        json.dump(scaling_analysis, f, indent=2)
    
    logger.info(f"Saved scaling analysis to {analysis_path}")
    return scaling_analysis

def main():
    """Main entry point for the scaling study."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run scaling study')
    parser.add_argument('--output_dir', type=str, default='data/results/scaling',
                      help='Output directory for results')
    parser.add_argument('--num_columns', type=str, default='1,2,4,8',
                      help='Comma-separated list of column counts')
    parser.add_argument('--hidden_dims', type=str, default='64,128,256',
                      help='Comma-separated list of hidden dimensions')
    parser.add_argument('--num_layers', type=str, default='2,4',
                      help='Comma-separated list of layer counts')
    parser.add_argument('--model_types', type=str, default='microcircuit,baseline,hybrid',
                      help='Comma-separated list of model types')
    parser.add_argument('--epochs', type=int, default=10,
                      help='Number of training epochs')
    
    args = parser.parse_args()
    
    # Parse ranges
    num_columns_range = [int(x) for x in args.num_columns.split(',')]
    hidden_dim_range = [int(x) for x in args.hidden_dims.split(',')]
    num_layers_range = [int(x) for x in args.num_layers.split(',')]
    model_types = [x.strip() for x in args.model_types.split(',')]
    
    # Base config
    base_config = ScalingConfig(
        variant_name='base',
        model_type='microcircuit',
        num_columns=1,
        hidden_dim=64,
        num_heads=4,
        num_layers=2,
        dropout=0.1,
        learning_rate=1e-4,
        batch_size=32,
        num_epochs=args.epochs,
        device='cpu',
        seed=42
    )
    
    # Generate configs
    configs = create_scaling_configs(
        base_config=base_config,
        num_columns_range=num_columns_range,
        hidden_dim_range=hidden_dim_range,
        num_layers_range=num_layers_range,
        model_types=model_types
    )
    
    # Run study
    logger.info(f"Starting scaling study with {len(configs)} configurations")
    results = run_scaling_study(configs, args.output_dir)
    
    # Save results
    results_path = os.path.join(args.output_dir, 'scaling_results.json')
    save_scaling_results(results, results_path)
    
    # Analyze scaling laws
    analyze_scaling_laws(results, args.output_dir)
    
    logger.info("Scaling study completed")
    return results

if __name__ == '__main__':
    main()