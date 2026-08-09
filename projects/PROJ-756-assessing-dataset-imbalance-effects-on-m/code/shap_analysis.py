import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
RANDOM_SEED = 42
N_SAMPLES = 5000  # Number of synthetic samples to generate
OUTPUT_DIR = Path("data/synthetic")
OUTPUT_FILE = OUTPUT_DIR / "ground_truth.parquet"
SCHEMA_FILE = Path("data/processed/descriptor_schema.json")


def load_descriptor_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load the descriptor schema extracted in T007b.
    Expects a JSON file containing column names and count.
    """
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema file not found: {schema_path}. "
            "Please ensure T007b-Schema-Extraction has been completed successfully."
        )
    
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    logger.info(f"Loaded schema from {schema_path}")
    logger.info(f"Schema keys: {list(schema.keys())}")
    
    return schema


def generate_physics_inspired_weights(feature_names: List[str], n_features: int) -> np.ndarray:
    """
    Dynamically generate known_weights based on a physics-inspired function.
    Simulates atomic number dependencies and element property interactions.
    
    The weights are designed to reflect realistic Magpie descriptor importance:
    - Electronegativity-based features get higher weights
    - Atomic radius features get moderate weights
    - Valence electron features get significant weights
    - Some features get near-zero weights (noise features)
    
    Returns an L2-normalized weight vector.
    """
    np.random.seed(RANDOM_SEED)
    
    # Initialize weights with a base distribution
    weights = np.zeros(n_features)
    
    # Create a pattern based on feature index to simulate physical dependencies
    # Features 0-10: High importance (representing key atomic properties)
    # Features 11-20: Moderate importance
    # Features 21+: Low importance (noise features)
    
    for i in range(n_features):
        if i < 10:
            # High importance: simulate strong atomic property influence
            weights[i] = 1.5 + 0.5 * np.sin(i * 0.5)
        elif i < 20:
            # Moderate importance
            weights[i] = 0.8 + 0.3 * np.cos(i * 0.3)
        else:
            # Low importance: mostly noise
            weights[i] = 0.1 * np.random.randn()
    
    # Add some specific non-linear interactions by boosting certain indices
    # Simulating that certain combinations of properties are more important
    interaction_indices = [0, 3, 7, 12, 15]
    for idx in interaction_indices:
        if idx < n_features:
            weights[idx] *= 1.3
    
    # L2 normalize the weights
    norm = np.linalg.norm(weights)
    if norm > 0:
        weights = weights / norm
    
    logger.info(f"Generated {n_features} physics-inspired weights")
    logger.info(f"Weight range: [{weights.min():.4f}, {weights.max():.4f}]")
    logger.info(f"Weight mean: {weights.mean():.4f}, std: {weights.std():.4f}")
    
    return weights


def generate_synthetic_target(X: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """
    Calculate target using the specified non-linear formula:
    target = sum(weight_i * x_i) + 0.5 * sum(x_i^2) + 0.3 * sum(x_i * x_{i+1})
    
    This creates a realistic, non-linear relationship between features and target.
    """
    n_samples = X.shape[0]
    n_features = X.shape[1]
    
    # Linear component: sum(weight_i * x_i)
    linear_term = X @ weights
    
    # Quadratic component: 0.5 * sum(x_i^2)
    quadratic_term = 0.5 * np.sum(X**2, axis=1)
    
    # Interaction component: 0.3 * sum(x_i * x_{i+1})
    interaction_term = np.zeros(n_samples)
    for i in range(n_features - 1):
        interaction_term += 0.3 * X[:, i] * X[:, i + 1]
    
    # Combine all terms
    target = linear_term + quadratic_term + interaction_term
    
    # Add small Gaussian noise for realism (signal-to-noise ratio ~ 20:1)
    noise = np.random.normal(0, 0.05 * target.std(), n_samples)
    target = target + noise
    
    logger.info(f"Generated target with shape {target.shape}")
    logger.info(f"Target stats: mean={target.mean():.4f}, std={target.std():.4f}, min={target.min():.4f}, max={target.max():.4f}")
    
    return target


def generate_synthetic_dataset(schema: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate a synthetic dataset with known non-linear feature weights.
    Uses Gaussian noise with fixed seed for reproducibility.
    """
    # Extract feature information from schema
    if 'columns' not in schema:
        raise ValueError("Schema must contain 'columns' key")
    
    feature_names = schema['columns']
    n_features = len(feature_names)
    
    if 'count' in schema:
        assert schema['count'] == n_features, "Schema count mismatch with columns length"
    
    logger.info(f"Generating synthetic dataset with {n_features} features")
    logger.info(f"First 5 features: {feature_names[:5]}")
    
    # Generate Gaussian noise features
    np.random.seed(RANDOM_SEED)
    X = np.random.randn(N_SAMPLES, n_features)
    
    # Generate physics-inspired weights
    weights = generate_physics_inspired_weights(feature_names, n_features)
    
    # Calculate target using non-linear formula
    target = generate_synthetic_target(X, weights)
    
    # Create DataFrame
    df = pd.DataFrame(X, columns=feature_names)
    df['target'] = target
    df['known_weights'] = list([weights])  # Store weights as a list for each row (will be exploded later)
    
    # Explode known_weights into separate columns for each feature
    weights_df = pd.DataFrame(weights.reshape(1, -1), columns=[f'weight_{i}' for i in range(n_features)])
    df = pd.concat([df, weights_df], axis=1)
    
    # Add metadata columns
    df['is_synthetic'] = True
    df['generation_seed'] = RANDOM_SEED
    
    logger.info(f"Generated synthetic dataset with shape {df.shape}")
    logger.info(f"Columns: {df.columns.tolist()}")
    
    return df


def validate_weights(df: pd.DataFrame, feature_names: List[str]) -> bool:
    """
    Validate that known_weights match the descriptor count.
    """
    n_features = len(feature_names)
    weight_columns = [col for col in df.columns if col.startswith('weight_')]
    
    if len(weight_columns) != n_features:
        raise ValueError(
            f"Weight count mismatch: expected {n_features} weights, got {len(weight_columns)}"
        )
    
    logger.info("Weight validation passed")
    return True


def save_ground_truth(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the synthetic dataset with ground truth weights to parquet.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Saved ground truth dataset to {output_path}")
    logger.info(f"File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")


def main():
    """
    Main entry point for T036: Generate synthetic ground truth dataset.
    """
    logger.info("=" * 60)
    logger.info("Starting T036: Generate Synthetic Ground Truth Dataset")
    logger.info("=" * 60)
    
    try:
        # Step 1: Load descriptor schema from T007b
        logger.info("Step 1: Loading descriptor schema...")
        schema = load_descriptor_schema(SCHEMA_FILE)
        
        # Step 2: Generate synthetic dataset
        logger.info("Step 2: Generating synthetic dataset...")
        df = generate_synthetic_dataset(schema)
        
        # Step 3: Validate weights
        logger.info("Step 3: Validating weights...")
        feature_names = schema['columns']
        validate_weights(df, feature_names)
        
        # Step 4: Save ground truth
        logger.info("Step 4: Saving ground truth dataset...")
        save_ground_truth(df, OUTPUT_FILE)
        
        logger.info("=" * 60)
        logger.info("T036 completed successfully!")
        logger.info(f"Output file: {OUTPUT_FILE}")
        logger.info(f"Dataset shape: {df.shape}")
        logger.info(f"Features: {len(feature_names)}")
        logger.info("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        logger.error("Please ensure T007b-Schema-Extraction has been completed.")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
