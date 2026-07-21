"""
T037: Generate analysis configuration snapshot for reproducibility.

This script records the exact random seeds, hyperparameters, and dataset
split ratios used for the specific run into data/processed/analysis_config.json.

It imports configuration from code/config.py and reads split metadata from
the existing splitter artifacts to ensure the snapshot reflects the actual
execution parameters.
"""
import os
import json
import logging
import random
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Import project configuration
from config import load_config_from_file, ensure_directories, validate_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_split_metadata(split_path: Path) -> Dict[str, Any]:
    """
    Load metadata about the dataset split if available.
    
    Args:
        split_path: Path to the split metadata file (if it exists)
        
    Returns:
        Dictionary containing split information
    """
    metadata = {
        "train_samples": None,
        "holdout_samples": None,
        "split_ratio": None,
        "stratification_field": "utility_score"
    }
    
    if not split_path.exists():
        logger.warning(f"Split metadata file not found at {split_path}. Using defaults.")
        return metadata
        
    try:
        with open(split_path, 'r') as f:
            data = json.load(f)
            metadata.update(data)
    except Exception as e:
        logger.warning(f"Could not load split metadata: {e}. Using defaults.")
        
    return metadata

def load_ablation_config(config_path: Path) -> Dict[str, Any]:
    """
    Load ablation configuration if available.
    
    Args:
        config_path: Path to the ablation config file
        
    Returns:
        Dictionary containing ablation configuration
    """
    if not config_path.exists():
        return {"status": "config_not_found"}
        
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load ablation config: {e}")
        return {"status": "load_error", "error": str(e)}

def generate_analysis_config(
    output_path: Path,
    custom_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a complete analysis configuration snapshot.
    
    Args:
        output_path: Path where the JSON config will be saved
        custom_config: Optional dictionary with custom parameters to override defaults
        
    Returns:
        The generated configuration dictionary
    """
    # Load base project configuration
    try:
        base_config = load_config_from_file()
    except Exception as e:
        logger.warning(f"Could not load base config: {e}. Using minimal defaults.")
        base_config = {}
        
    # Determine random seeds (from config or defaults)
    random_seed = custom_config.get('random_seed') if custom_config else None
    if random_seed is None:
        random_seed = base_config.get('RANDOM_SEED', 42)
        
    np_seed = custom_config.get('numpy_seed') if custom_config else None
    if np_seed is None:
        np_seed = base_config.get('NUMPY_SEED', random_seed)
        
    # Ensure seeds are set for reproducibility
    random.seed(random_seed)
    np.random.seed(np_seed)
    
    # Load split metadata
    split_metadata_path = output_path.parent / "split_metadata.json"
    split_info = load_split_metadata(split_metadata_path)
    
    # Load ablation config if available
    ablation_config_path = output_path.parent / "ablation_config.json"
    ablation_info = load_ablation_config(ablation_config_path)
    
    # Build the configuration snapshot
    config_snapshot = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "project_id": "PROJ-990-llmxive-follow-up-extending-agenticsts-a",
            "task_id": "T037",
            "version": "1.0.0"
        },
        "random_seeds": {
            "python_random": random_seed,
            "numpy_random": np_seed,
            "description": "Seeds used for all stochastic operations in this run"
        },
        "hyperparameters": {
            "token_budget": base_config.get('TOKEN_BUDGET', 4096),
            "min_context": base_config.get('MIN_CONTEXT', 256),
            "entropy_method": "shannon",
            "classifier_type": base_config.get('CLASSIFIER_TYPE', 'decision_tree'),
            "ablation_k": base_config.get('ABLATION_K', 5),
            "statistical_tests": {
                "paired_test": "mcnemar" if split_info.get('is_divergent') is False else "permutation",
                "token_test": "paired_ttest",
                "correction": "bonferroni"
            }
        },
        "dataset_split": {
            "train_samples": split_info.get('train_samples'),
            "holdout_samples": split_info.get('holdout_samples'),
            "split_ratio": split_info.get('split_ratio'),
            "stratification_field": split_info.get('stratification_field'),
            "split_seed": random_seed
        },
        "ablation_study": ablation_info,
        "reproducibility_notes": [
            "All random seeds are fixed for this run",
            "Dataset split is stratified by utility_score",
            "Statistical tests use Bonferroni correction",
            "Token budget enforcement is deterministic given seeds"
        ]
    }
    
    # Ensure output directory exists
    ensure_directories([output_path.parent])
    
    # Write the configuration to disk
    with open(output_path, 'w') as f:
        json.dump(config_snapshot, f, indent=2)
        
    logger.info(f"Analysis configuration saved to {output_path}")
    return config_snapshot

def main():
    """Main entry point for the analysis config generator."""
    output_path = Path("data/processed/analysis_config.json")
    
    logger.info(f"Generating analysis configuration snapshot to {output_path}")
    
    try:
        config = generate_analysis_config(output_path)
        logger.info("Successfully generated analysis configuration")
        print(f"Configuration saved to: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate analysis configuration: {e}")
        raise

if __name__ == "__main__":
    main()