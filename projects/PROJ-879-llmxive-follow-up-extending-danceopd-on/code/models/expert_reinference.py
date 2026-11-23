#!/usr/bin/env python
"""
T029a: Generate Velocity Vectors from Tree Routing.

This script generates velocity vectors based on tree predictions.
It loads the specific expert field logic/weights corresponding to the 
predicted routing label and re-runs the expert field to generate a NEW 
velocity vector.

Input: routing_label (predicted by tree), prompt_embedding, noise_level
Output: velocity_vector for each sample, saved to data/processed/tree_predicted_vectors.parquet
"""
import argparse
import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
import torch

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config
from models.expert_loader import get_expert_field_logic, get_known_expert_ids
from models.euler import EulerIntegrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_tree_predictions(
    input_path: str,
    tree_model_path: str
) -> pd.DataFrame:
    """
    Load the dataset with tree predictions.
    
    Args:
        input_path: Path to the parquet file containing tree predictions
        tree_model_path: Path to the trained tree model (for verification)
        
    Returns:
        DataFrame with predictions
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} samples from {input_path}")
    
    # Verify required columns
    required_cols = ['prompt_embedding', 'noise_level', 'predicted_routing_label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df

def generate_velocity_vectors(
    df: pd.DataFrame,
    config: Dict[str, Any]
) -> pd.DataFrame:
    """
    Generate velocity vectors based on tree-predicted routing labels.
    
    For each sample:
    1. Get the predicted routing label from the tree
    2. Load the corresponding expert field logic
    3. Re-run the expert field with the input state to generate a NEW velocity vector
    
    Args:
        df: DataFrame with prompt_embedding, noise_level, predicted_routing_label
        config: Configuration dictionary
        
    Returns:
        DataFrame with original columns plus 'velocity_vector'
    """
    known_expert_ids = get_known_expert_ids()
    logger.info(f"Known expert IDs: {known_expert_ids}")
    
    # Initialize integrator
    integrator = EulerIntegrator(
        step_size=config.get('step_size', 0.1),
        steps=config.get('steps', 10)
    )
    
    results = []
    undefined_count = 0
    valid_count = 0
    
    for idx, row in df.iterrows():
        if idx % 100 == 0:
            logger.info(f"Processing sample {idx}/{len(df)}")
        
        prompt_embedding = np.array(row['prompt_embedding'], dtype=np.float32)
        noise_level = float(row['noise_level'])
        predicted_label = row['predicted_routing_label']
        
        # Validate routing label
        if predicted_label not in known_expert_ids:
            logger.warning(f"Sample {idx}: Invalid routing label '{predicted_label}'. Skipping.")
            undefined_count += 1
            continue
        
        try:
            # Load expert field logic for the predicted label
            expert_logic = get_expert_field_logic(predicted_label)
            
            if expert_logic is None:
                logger.warning(f"Sample {idx}: Expert logic not found for '{predicted_label}'. Skipping.")
                undefined_count += 1
                continue
            
            # Generate NEW velocity vector using the expert field
            # Expert field signature: expert_field(routing_label, prompt_embedding, noise_level) -> velocity_vector
            velocity_vector = expert_logic(predicted_label, prompt_embedding, noise_level)
            
            # Validate velocity vector
            if velocity_vector is None or len(velocity_vector) == 0:
                logger.warning(f"Sample {idx}: Empty velocity vector for '{predicted_label}'. Skipping.")
                undefined_count += 1
                continue
            
            results.append({
                'prompt_embedding': prompt_embedding.tolist(),
                'noise_level': noise_level,
                'predicted_routing_label': predicted_label,
                'velocity_vector': velocity_vector.tolist()
            })
            valid_count += 1
            
        except Exception as e:
            logger.error(f"Sample {idx}: Error generating velocity vector for '{predicted_label}': {e}")
            undefined_count += 1
            continue
    
    logger.info(f"Generated {valid_count} valid velocity vectors, skipped {undefined_count} invalid samples")
    
    if valid_count == 0:
        raise RuntimeError("No valid velocity vectors were generated. Check expert logic and input data.")
    
    return pd.DataFrame(results)

def save_velocity_vectors(
    df: pd.DataFrame,
    output_path: str
) -> None:
    """
    Save the generated velocity vectors to a parquet file.
    
    Args:
        df: DataFrame with velocity vectors
        output_path: Path to save the output file
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} samples to {output_path}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate velocity vectors from tree routing predictions')
    parser.add_argument('--input', type=str, required=True,
                      help='Path to input parquet file with tree predictions')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to output parquet file for velocity vectors')
    parser.add_argument('--tree-model', type=str, required=True,
                      help='Path to trained tree model (for verification)')
    parser.add_argument('--config', type=str, default=None,
                      help='Path to config file (optional)')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = get_config()
        if args.config and os.path.exists(args.config):
            with open(args.config, 'r') as f:
                custom_config = json.load(f)
                config.update(custom_config)
        
        logger.info("Starting velocity vector generation from tree routing")
        
        # Load tree predictions
        df = load_tree_predictions(args.input, args.tree_model)
        
        # Generate velocity vectors
        velocity_df = generate_velocity_vectors(df, config)
        
        # Save results
        save_velocity_vectors(velocity_df, args.output)
        
        logger.info("Velocity vector generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error during velocity vector generation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
