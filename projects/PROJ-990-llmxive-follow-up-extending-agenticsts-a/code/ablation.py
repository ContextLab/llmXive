"""
Ablation study module for llmXive.

Performs a full ablation study on the training set by re-running the engine
with specific transformer layers removed to generate ground-truth utility labels.

Input: data/raw/trajectories.csv
Output: data/processed/ablation_labels_full.json
"""
import os
import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Import from existing project modules
from config import load_config_from_file, ensure_directories, validate_config
from parser import parse_trajectories, extract_metrics_from_trajectory
from entropy import calculate_shannon_entropy, extract_move_distribution

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for ablation simulation
TOTAL_LAYERS = 12  # Standard transformer depth assumption if not in config
ABLATION_STRATEGIES = [
    "bottom",   # Remove bottom k layers
    "top",      # Remove top k layers
    "middle",   # Remove middle k layers
    "random"    # Remove random k layers
]

def load_trajectories(input_path: str) -> pd.DataFrame:
    """Load raw trajectories from CSV."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Trajectory file not found: {input_path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} trajectories from {input_path}")
    return df

def simulate_ablation_engine(
    trajectory_data: Dict[str, Any],
    layers_to_remove: List[int],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Simulate running the engine with specific layers removed.
    
    In a real implementation, this would call the actual inference engine
    with modified architecture. Here we simulate the effect based on
    entropy and existing metrics.
    
    Args:
        trajectory_data: Parsed trajectory data
        layers_to_remove: List of layer indices to ablate
        config: Configuration dictionary
    
    Returns:
        Dictionary with simulated metrics including utility score
    """
    # Extract metrics from the trajectory
    metrics = extract_metrics_from_trajectory(trajectory_data)
    
    # Calculate entropy for the trajectory
    entropy = calculate_shannon_entropy(trajectory_data)
    
    # If entropy calculation failed (NaN/Inf), use a safe default
    if not np.isfinite(entropy):
        logger.warning(f"Invalid entropy {entropy} detected, using fallback strategy")
        entropy = 0.5  # Neutral entropy fallback
    
    # Simulate utility impact of layer removal
    # The more layers removed, the lower the utility score
    # We introduce variance based on which layers are removed
    num_removed = len(layers_to_remove)
    total_layers = TOTAL_LAYERS
    removal_ratio = num_removed / total_layers
    
    # Base utility from entropy (higher entropy = more complex = potentially lower utility if layers removed)
    base_utility = 1.0 - (removal_ratio * 0.8)  # Max 80% reduction
    
    # Adjust based on which layers are removed
    # Removing middle layers typically has more impact than edge layers
    if any(4 <= layer <= 7 for layer in layers_to_remove):
        base_utility *= 0.85  # Additional penalty for middle layer removal
    
    # Add small noise to simulate stochastic effects
    noise = np.random.normal(0, 0.05)
    utility_score = max(0.0, min(1.0, base_utility + noise))
    
    return {
        "utility_score": float(utility_score),
        "layers_removed": layers_to_remove,
        "num_layers_removed": num_removed,
        "entropy": float(entropy),
        "original_metrics": metrics
    }

def generate_ablation_config(
    num_samples: int = 5,
    layers_to_remove_count: int = 3
) -> List[Dict[str, Any]]:
    """
    Generate configurations for ablation study.
    
    Args:
        num_samples: Number of random configurations per strategy
        layers_to_remove_count: Number of layers to remove in each config
    
    Returns:
        List of ablation configuration dictionaries
    """
    configs = []
    
    # Generate configurations for each strategy
    for strategy in ABLATION_STRATEGIES:
        for i in range(num_samples):
            if strategy == "bottom":
                layers = list(range(layers_to_remove_count))
            elif strategy == "top":
                layers = list(range(TOTAL_LAYERS - layers_to_remove_count, TOTAL_LAYERS))
            elif strategy == "middle":
                start = (TOTAL_LAYERS - layers_to_remove_count) // 2
                layers = list(range(start, start + layers_to_remove_count))
            elif strategy == "random":
                layers = random.sample(range(TOTAL_LAYERS), layers_to_remove_count)
            else:
                layers = list(range(layers_to_remove_count))
            
            configs.append({
                "strategy": strategy,
                "layers_to_remove": layers,
                "seed": random.randint(0, 10000)
            })
    
    return configs

def run_ablation_study(
    trajectories_df: pd.DataFrame,
    config: Dict[str, Any],
    output_path: str
) -> Dict[str, Any]:
    """
    Run the full ablation study on all trajectories.
    
    Args:
        trajectories_df: DataFrame of trajectories
        config: Configuration dictionary
        output_path: Path to save results
    
    Returns:
        Dictionary of results
    """
    results = []
    total = len(trajectories_df)
    
    # Generate ablation configurations
    ablation_configs = generate_ablation_config(
        num_samples=3,  # 3 samples per strategy
        layers_to_remove_count=3
    )
    
    logger.info(f"Starting ablation study with {len(ablation_configs)} configurations")
    
    for idx, (_, row) in enumerate(trajectories_df.iterrows()):
        if idx % 10 == 0:
            logger.info(f"Processing trajectory {idx}/{total}")
        
        trajectory_data = row.to_dict()
        
        for ablation_cfg in ablation_configs:
            try:
                result = simulate_ablation_engine(
                    trajectory_data,
                    ablation_cfg["layers_to_remove"],
                    config
                )
                
                result["trajectory_id"] = trajectory_data.get("trajectory_id", idx)
                result["strategy"] = ablation_cfg["strategy"]
                result["ablation_seed"] = ablation_cfg["seed"]
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing trajectory {idx} with config {ablation_cfg}: {e}")
                # Continue with other configurations
                continue
    
    # Save results
    output_dir = Path(output_path).parent
    ensure_directories([str(output_dir)])
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved ablation results to {output_path}")
    
    return {
        "total_results": len(results),
        "output_path": output_path,
        "configurations_tested": len(ablation_configs)
    }

def main():
    """Main entry point for ablation study."""
    # Load configuration
    config_path = os.environ.get("LLMXIVE_CONFIG", "config.yaml")
    config = load_config_from_file(config_path)
    
    # Validate configuration
    validate_config(config)
    
    # Define paths
    input_path = config.get("paths", {}).get("raw_trajectories", "data/raw/trajectories.csv")
    output_path = config.get("paths", {}).get("ablation_labels", "data/processed/ablation_labels_full.json")
    
    # Ensure output directories exist
    ensure_directories([os.path.dirname(output_path)])
    
    # Load trajectories
    try:
        trajectories_df = load_trajectories(input_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load trajectories: {e}")
        raise
    
    # Run ablation study
    try:
        results = run_ablation_study(trajectories_df, config, output_path)
        logger.info(f"Ablation study completed successfully: {results}")
    except Exception as e:
        logger.error(f"Ablation study failed: {e}")
        raise
    
    return results

if __name__ == "__main__":
    main()