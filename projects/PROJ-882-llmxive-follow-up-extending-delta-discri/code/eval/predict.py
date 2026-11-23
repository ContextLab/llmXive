"""
T023: Generate predictions for the held-out test set and save to data/processed/predictions.json.

This script:
1. Loads the trained MLP model (data/processed/mlp_model.pt)
2. Loads the static features (data/processed/static_features.parquet)
3. Loads the ground truth coefficients (data/processed/delta_coefficients.json)
4. Splits data into train/test (using the same seed=42 logic as training)
5. Runs inference on the test set
6. Saves predictions to data/processed/predictions.json conforming to contracts/predictions.schema.yaml
"""

import os
import sys
import json
import logging
import argparse
import traceback
from pathlib import Path
from typing import Dict, Any, List, Tuple
import torch
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import get_config_summary
from models.mlp import DelTA_MLP

logger = logging.getLogger(__name__)

def load_model(model_path: str, input_dim: int) -> DelTA_MLP:
    """Load the trained MLP model."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Create a dummy model to load state dict
    model = DelTA_MLP(input_dim=input_dim, hidden_dim=64, output_dim=1)
    model.load_state_dict(torch.load(model_path, map_location='cpu', weights_only=True))
    model.eval()
    return model

def load_data(
    features_path: str,
    coefficients_path: str
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Load features and coefficients."""
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    if not os.path.exists(coefficients_path):
        raise FileNotFoundError(f"Coefficients file not found: {coefficients_path}")
    
    features_df = pd.read_parquet(features_path)
    with open(coefficients_path, 'r') as f:
        coefficients_data = json.load(f)
    
    return features_df, coefficients_data

def split_test_set(
    features_df: pd.DataFrame,
    coefficients_data: Dict[str, Any],
    test_ratio: float = 0.2,
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict], List[Dict]]:
    """
    Split data into train/test sets.
    Uses stratified sampling by example_id to ensure consistent split.
    """
    # Get unique example IDs
    example_ids = features_df['example_id'].unique()
    
    # Use numpy for reproducible splitting
    rng = np.random.default_rng(seed)
    rng.shuffle(example_ids)
    
    split_idx = int(len(example_ids) * (1 - test_ratio))
    train_ids = set(example_ids[:split_idx])
    test_ids = set(example_ids[split_idx:])
    
    # Split features
    train_features = features_df[features_df['example_id'].isin(train_ids)]
    test_features = features_df[features_df['example_id'].isin(test_ids)]
    
    # Split coefficients (filter to only test examples)
    test_coeffs = [
        coeff for coeff in coefficients_data['coefficients']
        if coeff['example_id'] in test_ids
    ]
    
    # Create a mapping from (example_id, token_id) to true coefficient
    true_coeff_map = {}
    for coeff in test_coeffs:
        key = (coeff['example_id'], coeff['token_id'])
        true_coeff_map[key] = coeff['coefficient']
    
    return train_features, test_features, test_coeffs, true_coeff_map

def run_inference(
    model: DelTA_MLP,
    test_features: pd.DataFrame,
    true_coeff_map: Dict[Tuple[int, int], float],
    device: str = 'cpu'
) -> List[Dict[str, Any]]:
    """Run model inference on test set and collect predictions."""
    model.to(device)
    predictions = []
    
    # Prepare data for inference
    # Group by example_id to process tokens together
    for example_id in test_features['example_id'].unique():
        example_df = test_features[test_features['example_id'] == example_id]
        
        # Extract feature vectors
        feature_vectors = []
        token_ids = []
        positions = []
        
        for _, row in example_df.iterrows():
            # Handle feature_vector which might be stored as string or list
            if isinstance(row['feature_vector'], str):
                # Parse string representation of list
                try:
                    fv = json.loads(row['feature_vector'])
                except json.JSONDecodeError:
                    # Fallback: try to evaluate
                    fv = eval(row['feature_vector'])
            else:
                fv = row['feature_vector']
            
            feature_vectors.append(fv)
            token_ids.append(row['token_id'])
            positions.append(row['position'])
        
        # Convert to tensor
        X = torch.tensor(np.array(feature_vectors), dtype=torch.float32).to(device)
        
        # Run inference
        with torch.no_grad():
            outputs = model(X)
            predicted_coefficients = outputs.squeeze().cpu().numpy()
        
        # Collect predictions
        for i, (token_id, pos, pred_coeff) in enumerate(zip(token_ids, positions, predicted_coefficients)):
          true_coeff = true_coeff_map.get((example_id, token_id), None)
          
          pred_record = {
              'example_id': int(example_id),
              'token_id': int(token_id),
              'position': int(pos),
              'predicted_coefficient': float(pred_coeff),
              'true_coefficient': float(true_coeff) if true_coeff is not None else None
          }
          predictions.append(pred_record)
    
    return predictions

def save_predictions(predictions: List[Dict], output_path: str) -> None:
    """Save predictions to JSON file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        'metadata': {
            'total_predictions': len(predictions),
            'schema_version': '1.0'
        },
        'predictions': predictions
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved {len(predictions)} predictions to {output_path}")

def validate_predictions(predictions: List[Dict]) -> bool:
    """Basic validation of predictions."""
    if not predictions:
        logger.error("No predictions generated")
        return False
    
    # Check required fields
    required_fields = ['example_id', 'token_id', 'predicted_coefficient']
    for pred in predictions:
        for field in required_fields:
            if field not in pred:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Check for NaN
        if np.isnan(pred['predicted_coefficient']):
            logger.error(f"NaN in predicted_coefficient for example {pred['example_id']}")
            return False
    
    return True

def main():
    """Main entry point for prediction generation."""
    parser = argparse.ArgumentParser(description='Generate predictions for test set')
    parser.add_argument('--model-path', type=str, default='data/processed/mlp_model.pt',
                      help='Path to trained model')
    parser.add_argument('--features-path', type=str, default='data/processed/static_features.parquet',
                      help='Path to static features')
    parser.add_argument('--coefficients-path', type=str, default='data/processed/delta_coefficients.json',
                      help='Path to ground truth coefficients')
    parser.add_argument('--output-path', type=str, default='data/processed/predictions.json',
                      help='Output path for predictions')
    parser.add_argument('--test-ratio', type=float, default=0.2,
                      help='Test set ratio')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed for splitting')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load configuration
        config = get_config_summary()
        logger.info(f"Using config: {config}")
        
        # Load model
        logger.info("Loading model...")
        # Get input dimension from config or features
        input_dim = config.get('feature_dim', 128)  # Default fallback
        
        # Try to determine input_dim from features if possible
        if os.path.exists(args.features_path):
            sample_features = pd.read_parquet(args.features_path).head(1)
            if 'feature_vector' in sample_features.columns:
                fv = sample_features.iloc[0]['feature_vector']
                if isinstance(fv, str):
                    fv = json.loads(fv)
                input_dim = len(fv)
                logger.info(f"Detected feature dimension: {input_dim}")
        
        model = load_model(args.model_path, input_dim)
        logger.info("Model loaded successfully")
        
        # Load data
        logger.info("Loading data...")
        features_df, coefficients_data = load_data(args.features_path, args.coefficients_path)
        logger.info(f"Loaded {len(features_df)} feature vectors and {len(coefficients_data['coefficients'])} coefficients")
        
        # Split data
        logger.info("Splitting into train/test sets...")
        train_features, test_features, test_coeffs, true_coeff_map = split_test_set(
            features_df, coefficients_data, args.test_ratio, args.seed
        )
        logger.info(f"Test set size: {len(test_features)} tokens from {len(set(test_features['example_id']))} examples")
        
        # Run inference
        logger.info("Running inference...")
        predictions = run_inference(model, test_features, true_coeff_map)
        
        # Validate
        if not validate_predictions(predictions):
            raise ValueError("Validation failed")
        
        # Save predictions
        logger.info("Saving predictions...")
        save_predictions(predictions, args.output_path)
        
        logger.info("Prediction generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error during prediction generation: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()