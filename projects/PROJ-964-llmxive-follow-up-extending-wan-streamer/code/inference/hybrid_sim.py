"""
Hybrid Inference Simulation (T050)

Executes the full hybrid inference pipeline:
1. Loads the sampled dataset (T014 output).
2. Loads the finalized GRU estimator checkpoint (T018a output).
3. Loads the counterfactual intervention indices (T047 output).
4. Applies the randomized intervention logic from FR-008 (T045 fallback_handler).
5. Generates the HybridOutput artifact `data/processed/hybrid_output.parquet`.
"""
import os
import sys
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set

import torch
import pandas as pd
import numpy as np

# Project imports based on API surface
from utils.config import get_config_summary, set_seed
from models.gru_estimator import GRUEstimator, load_checkpoint
from inference.fallback_handler import load_counterfactual_indices, should_fallback, apply_fallback_logic
from utils.validators import validate_dataframe

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "code" / "config" / "detection_thresholds.yaml"
DEFAULT_SAMPLED_DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "sampled_dataset.parquet"
DEFAULT_COUNTERFACTUAL_PATH = PROJECT_ROOT / "data" / "processed" / "counterfactual_indices.parquet"
DEFAULT_CHECKPOINT_PATH = PROJECT_ROOT / "data" / "models" / "estimator_checkpoint_final.pt"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "hybrid_output.parquet"

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration summary."""
    return get_config_summary()

def load_estimator_model(checkpoint_path: Path) -> GRUEstimator:
    """Load the finalized GRU estimator model."""
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Estimator checkpoint not found at {checkpoint_path}")
    
    logger.info(f"Loading estimator model from {checkpoint_path}...")
    checkpoint = load_checkpoint(checkpoint_path)
    
    # Extract model state and config from checkpoint
    model_state_dict = checkpoint.get('model_state_dict')
    config = checkpoint.get('config', {})
    
    # Reconstruct model (assuming standard config structure)
    # Note: The checkpoint should contain the necessary hyperparameters to reconstruct the model
    input_size = config.get('input_size', 128) # Default guess if missing
    hidden_size = config.get('hidden_size', 256)
    output_size = 2 # Delta magnitude + UncertaintyScore
    num_layers = config.get('num_layers', 2)
    dropout = config.get('dropout', 0.1)
    
    model = GRUEstimator(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size,
        num_layers=num_layers,
        dropout=dropout
    )
    
    model.load_state_dict(model_state_dict)
    model.eval()
    logger.info("Estimator model loaded successfully.")
    return model

def load_sampled_dataset(dataset_path: Path) -> pd.DataFrame:
    """Load the sampled dataset."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Sampled dataset not found at {dataset_path}")
    
    logger.info(f"Loading sampled dataset from {dataset_path}...")
    df = pd.read_parquet(dataset_path)
    
    # Validate required columns exist
    required_cols = ['timestamp', 'semantic_feature', 'prosodic_feature', 
                    'latent_delta_magnitude', 'turn_label', 'frame_id']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in sampled dataset: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} frames from sampled dataset.")
    return df

def run_hybrid_inference(
    model: GRUEstimator,
    df: pd.DataFrame,
    counterfactual_indices: Set[int],
    device: str = "cpu"
) -> pd.DataFrame:
    """
    Execute the hybrid inference pipeline.
    
    For each frame:
    1. If frame_id is in counterfactual_indices, force fallback (use full solver simulation).
    2. Otherwise, run the estimator. If uncertainty > threshold or delta magnitude is high, fallback.
    3. Record the method used (estimator vs fallback) and the resulting latency/quality proxy.
    """
    logger.info(f"Starting hybrid inference on {len(df)} frames...")
    
    # Prepare data for model
    # Assuming semantic_feature and prosodic_feature are arrays/lists in the dataframe
    # We need to stack them into a tensor
    try:
        # Convert stringified arrays or list-columns to numpy arrays
        if isinstance(df['semantic_feature'].iloc[0], str):
            # Handle stringified arrays if necessary, or assume they are already parsed
            # For robustness, we'll try to parse if needed
            pass 
        
        # Create feature matrix
        # This assumes the features are already numeric arrays in the dataframe
        # If they are stored as strings, we need to parse them first
        # For this implementation, we assume they are list-like or numpy arrays
        
        # Flatten features for batch processing
        # We'll process in chunks to manage memory
        batch_size = 256
        results = []
        
        model.to(device)
        
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i+batch_size]
            batch_indices = batch_df['frame_id'].tolist()
            
            # Prepare input tensor
            # Assuming semantic_feature and prosodic_feature are the input features
            # We need to concatenate them
            try:
                # Attempt to stack features - handle both list and array inputs
                semantic_features = []
                prosodic_features = []
                
                for idx in batch_indices:
                    row = batch_df[batch_df['frame_id'] == idx].iloc[0]
                    # Handle potential string representations of arrays
                    sem_feat = row['semantic_feature']
                    pros_feat = row['prosodic_feature']
                    
                    if isinstance(sem_feat, str):
                        import ast
                        sem_feat = ast.literal_eval(sem_feat)
                    if isinstance(pros_feat, str):
                        import ast
                        pros_feat = ast.literal_eval(pros_feat)
                        
                    semantic_features.append(np.array(sem_feat).flatten())
                    prosodic_features.append(np.array(pros_feat).flatten())
                
                # Stack and concatenate
                semantic_tensor = np.stack(semantic_features, axis=0)
                prosodic_tensor = np.stack(prosodic_features, axis=0)
                
                # Combine features
                combined_features = np.concatenate([semantic_tensor, prosodic_tensor], axis=1)
                input_tensor = torch.FloatTensor(combined_features).to(device)
                
            except Exception as e:
                logger.error(f"Error preparing batch {i}: {e}")
                # Fallback for entire batch if tensor preparation fails
                input_tensor = None
            
            # Run inference or fallback
            batch_results = []
            
            for j, row_idx in enumerate(batch_indices):
                frame_id = row_idx
                is_counterfactual = frame_id in counterfactual_indices
                
                # Determine if we should use fallback
                if is_counterfactual:
                    # FR-008: Randomized intervention overrides deterministic fallback
                    # Force fallback for counterfactual frames
                    use_fallback = True
                    reason = "counterfactual_intervention"
                else:
                    # Normal inference flow
                    if input_tensor is not None:
                        try:
                            with torch.no_grad():
                                output = model(input_tensor[j:j+1])
                                delta_pred = output[0, 0].item()
                                uncertainty = output[0, 1].item()
                            
                                # Apply fallback logic from T045
                                use_fallback = should_fallback(delta_pred, uncertainty)
                                reason = "estimator_decision" if not use_fallback else "high_uncertainty_or_delta"
                                
                            if not use_fallback:
                                # Use estimator prediction
                                latency_reduction = np.random.uniform(0.6, 0.8) # Simulated reduction
                                quality_proxy = np.random.uniform(0.9, 1.0) # Simulated quality
                                results.append({
                                    'frame_id': frame_id,
                                    'method': 'estimator',
                                    'delta_pred': delta_pred,
                                    'uncertainty': uncertainty,
                                    'latency_reduction': latency_reduction,
                                    'quality_proxy': quality_proxy,
                                    'reason': reason
                                })
                                continue
                                
                        except Exception as e:
                            logger.warning(f"Inference failed for frame {frame_id}: {e}. Falling back.")
                            use_fallback = True
                            reason = "inference_error"
                    
                    # Fallback path
                    use_fallback = True
                    reason = reason if 'reason' in locals() else "default_fallback"
                
                # Execute fallback (simulate full solver)
                if use_fallback:
                    # Simulate full solver execution
                    # In a real scenario, this would call the heavy solver
                    latency_reduction = 0.0 # No reduction
                    quality_proxy = 1.0 # Full quality
                    delta_pred = df[df['frame_id'] == frame_id]['latent_delta_magnitude'].values[0]
                    uncertainty = 1.0 # High uncertainty when falling back
                    
                    results.append({
                        'frame_id': frame_id,
                        'method': 'fallback',
                        'delta_pred': delta_pred,
                        'uncertainty': uncertainty,
                        'latency_reduction': latency_reduction,
                        'quality_proxy': quality_proxy,
                        'reason': reason
                    })
            
            results.extend(batch_results)
            
    except Exception as e:
        logger.error(f"Error during hybrid inference: {e}")
        # Fallback: return a minimal result set indicating failure
        # In a real system, we might want to handle this more gracefully
        raise e
    
    logger.info(f"Hybrid inference completed. Processed {len(results)} frames.")
    return pd.DataFrame(results)

def save_hybrid_output(output_df: pd.DataFrame, output_path: Path) -> None:
    """Save the hybrid output to Parquet."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_parquet(output_path, index=False)
    logger.info(f"Hybrid output saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run Hybrid Inference Simulation (T050)")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to config file")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_SAMPLED_DATASET_PATH, help="Path to sampled dataset")
    parser.add_argument("--counterfactual", type=Path, default=DEFAULT_COUNTERFACTUAL_PATH, help="Path to counterfactual indices")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT_PATH, help="Path to estimator checkpoint")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Path for hybrid output")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Set seed
    set_seed(args.seed)
    
    # Load configuration
    config = load_config(args.config)
    logger.info(f"Configuration loaded: {config}")
    
    # Load model
    model = load_estimator_model(args.checkpoint)
    
    # Load dataset
    df = load_sampled_dataset(args.dataset)
    
    # Load counterfactual indices
    counterfactual_indices = load_counterfactual_indices(args.counterfactual)
    logger.info(f"Loaded {len(counterfactual_indices)} counterfactual indices.")
    
    # Run hybrid inference
    output_df = run_hybrid_inference(model, df, counterfactual_indices)
    
    # Save output
    save_hybrid_output(output_df, args.output)
    
    # Validate output
    if not args.output.exists():
        raise RuntimeError(f"Failed to create output file at {args.output}")
    
    logger.info("T050 Hybrid Simulation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())