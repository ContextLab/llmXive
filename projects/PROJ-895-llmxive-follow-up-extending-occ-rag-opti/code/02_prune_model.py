"""
Module: 02_prune_model.py
Task: T016
Description: Construct the pruned OCC-RAG model by retaining only the top CONFIG.RETENTION_PCT
             of parameters identified in sensitivity_results.csv and zeroing out the rest.

Dependencies:
  - utils.masking (for model loading utilities)
  - 00_config (for configuration)
  - pandas (for CSV parsing)
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any

import torch
import pandas as pd
from transformers import AutoModelForCausalLM, AutoConfig

# Adjust imports to work within the project structure
# Assuming this script runs from the project root or code/ directory
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.masking import load_model_layer_by_layer
from code_00_config import Config, validate_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/pruning_config.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def parse_param_id(param_id: str) -> Tuple[int, str, int]:
    """
    Parse the param_id string 'layer_id.param_type.param_index' into components.
    
    Args:
        param_id: String in format 'L.P.I'
    
    Returns:
        Tuple of (layer_id, param_type, param_index)
    """
    parts = param_id.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid param_id format: {param_id}. Expected 'layer_id.param_type.param_index'")
    
    layer_id = int(parts[0])
    param_type = parts[1]
    param_index = int(parts[2])
    
    return layer_id, param_type, param_index

def get_model_parameter_map(model: AutoModelForCausalLM) -> Dict[str, torch.nn.Parameter]:
    """
    Create a mapping from param_id to the actual parameter object in the model.
    
    Args:
        model: The loaded transformer model
    
    Returns:
        Dictionary mapping 'layer_id.param_type.param_index' to torch.nn.Parameter
    """
    param_map = {}
    
    for name, param in model.named_parameters():
        # Parse the parameter name to extract layer info
        # Expected format: model.layers.{layer_id}.{param_type}.{rest}
        # e.g., model.layers.0.self_attn.q_proj.weight
        # e.g., model.layers.0.mlp.up_proj.weight
        
        parts = name.split('.')
        if not name.startswith('model.layers.'):
            continue
        
        try:
            layer_idx = int(parts[2])
            param_type = parts[3]
            
            # For weights, we might have .weight at the end
            # For bias, we might have .bias at the end
            # We'll use the index of the weight/bias tensor within the module
            if param_type in ['self_attn', 'mlp']:
                # Handle nested structures
                if len(parts) >= 5:
                    sub_module = parts[4]
                    # Create a unique identifier for each parameter within the sub-module
                    # We'll use a counter approach or index based on parameter order
                    pass
            
            # For simplicity, we'll use the full path after 'model.layers.{layer_id}'
            # and create a param_id that matches our sensitivity results format
            # This requires mapping the actual parameter names to our expected format
            
        except (IndexError, ValueError):
            continue
    
    # Alternative approach: iterate through model layers and map parameters
    if hasattr(model, 'model') and hasattr(model.model, 'layers'):
        for layer_idx, layer in enumerate(model.model.layers):
            # Attention parameters
            if hasattr(layer, 'self_attn'):
                attn = layer.self_attn
                for param_name, param in attn.named_parameters():
                    # Map to our expected format
                    # e.g., q_proj.weight -> q_proj
                    if 'weight' in param_name:
                        base_name = param_name.replace('.weight', '')
                        param_id = f"{layer_idx}.{base_name}.0"  # Using 0 as index for simplicity
                        param_map[param_id] = param
                    elif 'bias' in param_name:
                        base_name = param_name.replace('.bias', '')
                        param_id = f"{layer_idx}.{base_name}.1"
                        param_map[param_id] = param
            
            # MLP parameters
            if hasattr(layer, 'mlp'):
                mlp = layer.mlp
                for param_name, param in mlp.named_parameters():
                    if 'weight' in param_name:
                        base_name = param_name.replace('.weight', '')
                        param_id = f"{layer_idx}.{base_name}.0"
                        param_map[param_id] = param
                    elif 'bias' in param_name:
                        base_name = param_name.replace('.bias', '')
                        param_id = f"{layer_idx}.{base_name}.1"
                        param_map[param_id] = param
    
    return param_map

def load_sensitivity_results(csv_path: str, retention_pct: float) -> List[str]:
    """
    Load sensitivity results and identify the top parameters to retain.
    
    Args:
        csv_path: Path to sensitivity_results.csv
        retention_pct: Percentage of parameters to retain (0.0 to 1.0)
    
    Returns:
        List of param_ids to retain (top sensitivity scores)
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Sensitivity results file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    required_columns = ['param_id', 'sensitivity_score']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Sensitivity results missing required columns: {missing_cols}")
    
    # Sort by sensitivity score descending
    df_sorted = df.sort_values('sensitivity_score', ascending=False)
    
    # Calculate number of parameters to retain
    total_params = len(df_sorted)
    num_retain = int(total_params * retention_pct)
    
    if num_retain == 0 and retention_pct > 0:
        num_retain = 1  # At least retain one parameter
    
    # Get top parameters
    top_params = df_sorted.head(num_retain)['param_id'].tolist()
    
    logger.info(f"Loaded {total_params} parameters from {csv_path}")
    logger.info(f"Retention percentage: {retention_pct*100:.2f}%")
    logger.info(f"Number of parameters to retain: {num_retain}")
    
    return top_params

def apply_pruning_mask(model: AutoModelForCausalLM, params_to_retain: List[str]) -> int:
    """
    Apply pruning mask to the model by zeroing out parameters not in the retain list.
    
    Args:
        model: The model to prune
        params_to_retain: List of param_ids to keep
    
    Returns:
        Number of parameters pruned
    """
    param_map = get_model_parameter_map(model)
    params_to_retain_set = set(params_to_retain)
    
    pruned_count = 0
    total_count = 0
    
    for param_id, param in param_map.items():
        total_count += 1
        if param_id not in params_to_retain_set:
            # Zero out the parameter
            with torch.no_grad():
                param.zero_()
            pruned_count += 1
    
    logger.info(f"Pruning complete: {pruned_count} out of {total_count} parameters zeroed")
    return pruned_count

def save_pruned_model(model: AutoModelForCausalLM, output_path: str, config: Config):
    """
    Save the pruned model weights.
    
    Args:
        model: The pruned model
        output_path: Path to save the model weights
        config: Configuration object
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save model weights
    torch.save(model.state_dict(), output_path)
    logger.info(f"Pruned model weights saved to {output_path}")
    
    # Save pruning configuration
    pruning_config = {
        'retention_pct': config.RETENTION_PCT,
        'model_name': config.MODEL_NAME,
        'output_file': output_path,
        'pruning_timestamp': str(pd.Timestamp.now())
    }
    
    config_path = output_path.replace('.pt', '_config.json')
    with open(config_path, 'w') as f:
        json.dump(pruning_config, f, indent=2)
    
    logger.info(f"Pruning configuration saved to {config_path}")

def main():
    """
    Main function to execute the pruning process.
    """
    logger.info("Starting model pruning process (T016)")
    
    # Validate configuration
    config = Config()
    validate_config(config)
    
    if config.RETENTION_PCT is None or config.RETENTION_PCT <= 0 or config.RETENTION_PCT > 1:
        raise ValueError(f"Invalid RETENTION_PCT in config: {config.RETENTION_PCT}. Must be between 0 and 1.")
    
    # Define paths
    sensitivity_results_path = 'data/processed/sensitivity_results.csv'
    model_name = config.MODEL_NAME
    output_filename = f"OCC-RAG-Pruned-{config.RETENTION_PCT:.2f}B.pt"
    output_path = f"data/processed/{output_filename}"
    
    # Load sensitivity results
    logger.info(f"Loading sensitivity results from {sensitivity_results_path}")
    params_to_retain = load_sensitivity_results(sensitivity_results_path, config.RETENTION_PCT)
    
    # Load the model
    logger.info(f"Loading model: {model_name}")
    try:
        model = load_model_layer_by_layer(model_name)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    
    # Apply pruning mask
    logger.info("Applying pruning mask")
    pruned_count = apply_pruning_mask(model, params_to_retain)
    
    # Save the pruned model
    logger.info(f"Saving pruned model to {output_path}")
    save_pruned_model(model, output_path, config)
    
    # Log final summary
    logger.info("=" * 50)
    logger.info("Pruning Summary:")
    logger.info(f"  Model: {model_name}")
    logger.info(f"  Retention Percentage: {config.RETENTION_PCT*100:.2f}%")
    logger.info(f"  Parameters Retained: {len(params_to_retain)}")
    logger.info(f"  Parameters Pruned: {pruned_count}")
    logger.info(f"  Output File: {output_path}")
    logger.info("=" * 50)
    
    logger.info("Model pruning completed successfully")

if __name__ == "__main__":
    main()
