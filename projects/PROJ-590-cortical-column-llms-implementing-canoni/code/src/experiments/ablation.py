import json
import os
import logging
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

import torch
import torch.nn as nn

from src.models.microcircuit import MicrocircuitColumn, create_microcircuit_column, MicrocircuitColumnConfig
from src.models.hybrid_network import HybridNetwork, create_hybrid_network
from src.training.homeostasis import HomeostasisConfig

logger = logging.getLogger(__name__)

@dataclass
class AblationConfig:
    """Configuration for a specific ablation experiment."""
    name: str
    description: str
    model_type: str  # 'microcircuit', 'hybrid', 'baseline'
    ablation_type: str  # 'remove_l23', 'remove_l5', 'disable_homeostasis', 'random_connectivity', 'full'
    microcircuit_config: Optional[Dict[str, Any]] = None
    homeostasis_config: Optional[Dict[str, Any]] = None
    expected_metric_impact: float = 0.0  # Optional: expected change in MAE
    parameter_count: int = 0

@dataclass
class AblationResult:
    """Result of an ablation experiment."""
    config_name: str
    ablation_type: str
    model_type: str
    final_mae: float
    initial_mae: float
    parameter_count: int
    training_time_seconds: float
    homeostasis_active: bool
    timestamp: str
    details: Dict[str, Any]

def generate_ablation_configs(
    base_config: Optional[MicrocircuitColumnConfig] = None,
    homeostasis_config: Optional[HomeostasisConfig] = None
) -> List[AblationConfig]:
    """
    Generate a comprehensive set of ablation configurations for the microcircuit study.

    This function implements the systematic ablation plan required for US3.
    It creates configurations that:
    1. Remove specific cortical layers (L2/3, L5, L6)
    2. Disable homeostatic scaling
    3. Replace structured connectivity with random connectivity
    4. Test hybrid network variants
    5. Include a full baseline (no ablation)

    Args:
        base_config: Optional base MicrocircuitColumnConfig to derive from.
                     If None, defaults are used.
        homeostasis_config: Optional HomeostasisConfig. If None, defaults used.

    Returns:
        List[AblationConfig]: A list of distinct ablation configurations.
    """
    configs = []

    # Default configurations if not provided
    if base_config is None:
        base_config = MicrocircuitColumnConfig(
            input_dim=128,
            hidden_dim=256,
            output_dim=64,
            num_heads=4,
            dropout=0.1
        )

    if homeostasis_config is None:
        homeostasis_config = HomeostasisConfig(
            target_ei_ratio=4.0,
            decay_rate=0.01,
            scaling_window=100
        )

    # 1. Full Baseline (No ablation)
    configs.append(AblationConfig(
        name="full_baseline",
        description="Full microcircuit with all layers and homeostasis enabled",
        model_type="microcircuit",
        ablation_type="full",
        microcircuit_config=asdict(base_config),
        homeostasis_config=asdict(homeostasis_config),
        expected_metric_impact=0.0
    ))

    # 2. Ablate L2/3 Layer (Remove feedback/feedforward integration)
    l23_ablated_config = asdict(base_config)
    l23_ablated_config['l23_enabled'] = False
    configs.append(AblationConfig(
        name="ablate_l23",
        description="Remove L2/3 layer to test role in top-down integration",
        model_type="microcircuit",
        ablation_type="remove_l23",
        microcircuit_config=l23_ablated_config,
        homeostasis_config=asdict(homeostasis_config),
        expected_metric_impact=0.15
    ))

    # 3. Ablate L5 Layer (Remove output generation)
    l5_ablated_config = asdict(base_config)
    l5_ablated_config['l5_enabled'] = False
    configs.append(AblationConfig(
        name="ablate_l5",
        description="Remove L5 layer to test role in output projection",
        model_type="microcircuit",
        ablation_type="remove_l5",
        microcircuit_config=l5_ablated_config,
        homeostasis_config=asdict(homeostasis_config),
        expected_metric_impact=0.25
    ))

    # 4. Disable Homeostasis (Test E/I balance necessity)
    no_homeo_config = asdict(base_config)
    no_homeo_homeo = asdict(homeostasis_config)
    no_homeo_homeo['enabled'] = False
    configs.append(AblationConfig(
        name="no_homeostasis",
        description="Disable homeostatic scaling to test E/I balance importance",
        model_type="microcircuit",
        ablation_type="disable_homeostasis",
        microcircuit_config=no_homeo_config,
        homeostasis_config=no_homeo_homeo,
        expected_metric_impact=0.10
    ))

    # 5. Random Connectivity (Test structured topology necessity)
    random_conn_config = asdict(base_config)
    random_conn_config['use_laminar_mask'] = False
    configs.append(AblationConfig(
        name="random_connectivity",
        description="Replace laminar connectivity with random connections",
        model_type="microcircuit",
        ablation_type="random_connectivity",
        microcircuit_config=random_conn_config,
        homeostasis_config=asdict(homeostasis_config),
        expected_metric_impact=0.20
    ))

    # 6. Hybrid Network (Compare with standard attention)
    configs.append(AblationConfig(
        name="hybrid_baseline",
        description="Hybrid network with cortical-inspired attention",
        model_type="hybrid",
        ablation_type="full",
        microcircuit_config=asdict(base_config),
        homeostasis_config=asdict(homeostasis_config),
        expected_metric_impact=0.05
    ))

    # 7. Partial Homeostasis (Only scaling, no E/I enforcement)
    partial_homeo_config = asdict(homeostasis_config)
    partial_homeo_config['enforce_ei_ratio'] = False
    configs.append(AblationConfig(
        name="partial_homeostasis",
        description="Homeostatic scaling without strict E/I ratio enforcement",
        model_type="microcircuit",
        ablation_type="partial_homeostasis",
        microcircuit_config=asdict(base_config),
        homeostasis_config=partial_homeo_config,
        expected_metric_impact=0.08
    ))

    logger.info(f"Generated {len(configs)} ablation configurations")
    return configs

def save_ablation_configs(configs: List[AblationConfig], output_path: str) -> None:
    """Save ablation configurations to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    data = [asdict(c) for c in configs]
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved ablation configs to {output_path}")

def load_ablation_configs(input_path: str) -> List[AblationConfig]:
    """Load ablation configurations from a JSON file."""
    with open(input_path, 'r') as f:
        data = json.load(f)
    configs = [AblationConfig(**item) for item in data]
    logger.info(f"Loaded {len(configs)} ablation configs from {input_path}")
    return configs

def create_ablated_microcircuit_column(config: AblationConfig) -> MicrocircuitColumn:
    """Create a MicrocircuitColumn based on an ablation configuration."""
    if config.model_type != "microcircuit":
        raise ValueError(f"Expected model_type 'microcircuit', got '{config.model_type}'")

    if config.microcircuit_config is None:
        raise ValueError("microcircuit_config is required for microcircuit model type")

    model_config = MicrocircuitColumnConfig(**config.microcircuit_config)
    
    # Handle homeostasis config
    if config.homeostasis_config:
        homeo_cfg = HomeostasisConfig(**config.homeostasis_config)
    else:
        homeo_cfg = HomeostasisConfig()

    # Create the model
    model = create_microcircuit_column(model_config, homeo_cfg)
    
    # Count parameters
    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return model, param_count

def create_ablated_hybrid_network(config: AblationConfig) -> HybridNetwork:
    """Create a HybridNetwork based on an ablation configuration."""
    if config.model_type != "hybrid":
        raise ValueError(f"Expected model_type 'hybrid', got '{config.model_type}'")

    if config.microcircuit_config is None:
        raise ValueError("microcircuit_config is required for hybrid model type")

    model_config = MicrocircuitColumnConfig(**config.microcircuit_config)
    model = create_hybrid_network(model_config)
    
    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return model, param_count

def run_ablation_experiment(
    config: AblationConfig,
    train_data: torch.Tensor,
    test_data: torch.Tensor,
    device: str = "cpu"
) -> AblationResult:
    """
    Run a single ablation experiment.

    This is a placeholder for the actual training logic. In a real implementation,
    this would train the model, evaluate it, and return metrics.
    """
    start_time = time.time()
    
    # Create model
    if config.model_type == "microcircuit":
        model, param_count = create_ablated_microcircuit_column(config)
    elif config.model_type == "hybrid":
        model, param_count = create_ablated_hybrid_network(config)
    else:
        raise ValueError(f"Unsupported model type: {config.model_type}")

    model.to(device)
    model.train()

    # Placeholder training loop (in real implementation, this would be the full training)
    # We simulate a training run to return realistic-looking metrics
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()

    # Simulate training for a few steps to get a "real" result
    for _ in range(5):  # Just a few steps for the ablation config generation task
        optimizer.zero_grad()
        # Dummy forward pass
        dummy_input = torch.randn(4, 10, train_data.shape[-1], device=device)
        output = model(dummy_input)
        loss = criterion(output, output)  # Dummy loss
        loss.backward()
        optimizer.step()

    training_time = time.time() - start_time

    # Simulate metrics (in real implementation, these would be actual results)
    # The ablation_config generation task is about creating the CONFIGS, 
    # not running the full study (that's T025b). 
    # However, we return a result structure for completeness.
    result = AblationResult(
        config_name=config.name,
        ablation_type=config.ablation_type,
        model_type=config.model_type,
        final_mae=0.0,  # Placeholder
        initial_mae=0.0,  # Placeholder
        parameter_count=param_count,
        training_time_seconds=training_time,
        homeostasis_active=config.homeostasis_config is not None and config.homeostasis_config.get('enabled', True),
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        details={"status": "config_generated", "note": "Training not executed in config generation phase"}
    )

    return result

def run_ablation_study(
    configs: List[AblationConfig],
    train_data: torch.Tensor,
    test_data: torch.Tensor,
    output_dir: str = "data/results/ablation",
    device: str = "cpu"
) -> List[AblationResult]:
    """Run the full ablation study."""
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for i, config in enumerate(configs):
        logger.info(f"Running ablation {i+1}/{len(configs)}: {config.name}")
        try:
            result = run_ablation_experiment(config, train_data, test_data, device)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed ablation {config.name}: {e}")
            # Create a failed result
            results.append(AblationResult(
                config_name=config.name,
                ablation_type=config.ablation_type,
                model_type=config.model_type,
                final_mae=-1.0,
                initial_mae=-1.0,
                parameter_count=0,
                training_time_seconds=0.0,
                homeostasis_active=False,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                details={"error": str(e)}
            ))

    # Save results
    results_path = os.path.join(output_dir, "ablation_results.json")
    with open(results_path, 'w') as f:
        json.dump([asdict(r) for r in results], f, indent=2)

    logger.info(f"Abalation study complete. Results saved to {results_path}")
    return results

def main():
    """Main entry point for ablation config generation."""
    logging.basicConfig(level=logging.INFO)
    
    # Generate configs
    configs = generate_ablation_configs()
    
    # Save to default location
    output_path = "data/configs/ablation_configs.json"
    save_ablation_configs(configs, output_path)
    
    print(f"Generated {len(configs)} ablation configurations.")
    print(f"Saved to: {output_path}")
    
    # Print summary
    for cfg in configs:
        print(f"  - {cfg.name}: {cfg.description}")

if __name__ == "__main__":
    main()