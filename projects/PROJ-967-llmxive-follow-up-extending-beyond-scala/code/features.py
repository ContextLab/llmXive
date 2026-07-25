import argparse
import json
import logging
import os
import sys
import math
import numpy as np
import pandas as pd

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def load_aligned_data(ingestion_path: str) -> pd.DataFrame:
    """
    Load the aligned dataset produced by ingest.py.
    Expected columns: prompt, image_path, teacher_logits (list), student_scalar,
    human_annotations (dict), primary_dimension.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Loading aligned data from {ingestion_path}")
    
    if not os.path.exists(ingestion_path):
        raise FileNotFoundError(f"Aligned data file not found: {ingestion_path}")
    
    # Assuming the output of ingest.py is a CSV or JSONL format
    # Based on typical pipeline outputs, we expect a CSV with stringified lists/dicts
    # or a JSON file. Let's handle JSON first as it's safer for nested structures.
    if ingestion_path.endswith('.json'):
        with open(ingestion_path, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    elif ingestion_path.endswith('.csv'):
        df = pd.read_csv(ingestion_path)
        # If teacher_logits are stored as strings "[x, y, z]", parse them
        if 'teacher_logits' in df.columns:
            def parse_list(s):
                if isinstance(s, list): return s
                try:
                    return json.loads(s)
                except:
                    return []
            df['teacher_logits'] = df['teacher_logits'].apply(parse_list)
        if 'human_annotations' in df.columns:
            def parse_dict(s):
                if isinstance(s, dict): return s
                try:
                    return json.loads(s)
                except:
                    return {}
            df['human_annotations'] = df['human_annotations'].apply(parse_dict)
        return df
    else:
        raise ValueError(f"Unsupported file format: {ingestion_path}")

def calculate_variance_and_range(scores: list) -> dict:
    """Calculate variance and range for a list of scores."""
    if not scores:
        return {"variance": 0.0, "range": 0.0}
    arr = np.array(scores)
    variance = float(np.var(arr))
    range_val = float(np.max(arr) - np.min(arr))
    return {"variance": variance, "range": range_val}

def calculate_entropy(scores: list) -> float:
    """Calculate entropy of a distribution. Treats scores as unnormalized probabilities."""
    if not scores:
        return 0.0
    arr = np.array(scores)
    # Normalize to probabilities
    total = np.sum(arr)
    if total == 0:
        return 0.0
    probs = arr / total
    # Filter out zeros to avoid log(0)
    probs = probs[probs > 0]
    entropy = -np.sum(probs * np.log(probs))
    return float(entropy)

def calculate_skewness_and_kurtosis(scores: list) -> dict:
    """Calculate skewness and kurtosis."""
    if len(scores) < 4:
        return {"skewness": 0.0, "kurtosis": 0.0}
    arr = np.array(scores)
    # Use scipy if available, otherwise fallback to manual or numpy
    try:
        from scipy.stats import skew, kurtosis
        return {
            "skewness": float(skew(arr)),
            "kurtosis": float(kurtosis(arr))
        }
    except ImportError:
        # Fallback manual calculation
        mean = np.mean(arr)
        std = np.std(arr)
        if std == 0:
            return {"skewness": 0.0, "kurtosis": 0.0}
        skewness = np.mean(((arr - mean) / std) ** 3)
        kurtosis = np.mean(((arr - mean) / std) ** 4) - 3
        return {"skewness": float(skewness), "kurtosis": float(kurtosis)}

def calculate_per_sample_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate per-sample statistical features (variance, entropy, skewness, kurtosis).
    This corresponds to T022a.
    """
    logger = logging.getLogger(__name__)
    logger.info("Calculating per-sample statistics (T022a)...")
    
    results = []
    for idx, row in df.iterrows():
        logits = row.get('teacher_logits', [])
        if not logits:
            stats = {
                "sample_id": row.get('sample_id', idx),
                "variance": 0.0,
                "entropy": 0.0,
                "skewness": 0.0,
                "kurtosis": 0.0
            }
        else:
            var_range = calculate_variance_and_range(logits)
            ent = calculate_entropy(logits)
            skew_kurt = calculate_skewness_and_kurtosis(logits)
            stats = {
                "sample_id": row.get('sample_id', idx),
                "variance": var_range["variance"],
                "entropy": ent,
                "skewness": skew_kurt["skewness"],
                "kurtosis": skew_kurt["kurtosis"]
            }
        results.append(stats)
    
    return pd.DataFrame(results)

def calculate_global_entanglement_score(df: pd.DataFrame) -> float:
    """
    Implement T022b: Global Covariance Matrix and Dominant Eigenvalue.
    
    1. Extract teacher score vectors for the entire dataset.
    2. Compute the 4x4 covariance matrix of these vectors.
    3. Extract the dominant eigenvalue (largest eigenvalue).
    4. Return as a single scalar.
    """
    logger = logging.getLogger(__name__)
    logger.info("Calculating Global Covariance Matrix and Dominant Eigenvalue (T022b)...")
    
    # Collect all teacher logits
    all_logits = []
    for _, row in df.iterrows():
        logits = row.get('teacher_logits', [])
        if len(logits) == 4: # Ensure we have exactly 4 dimensions
            all_logits.append(logits)
        elif len(logits) > 0:
            # Pad or truncate if necessary, but spec implies 4 dims
            # For robustness, we take the first 4 or pad with 0
            if len(logits) < 4:
                logits = list(logits) + [0.0] * (4 - len(logits))
            else:
                logits = logits[:4]
            all_logits.append(logits)
    
    if len(all_logits) == 0:
        logger.warning("No valid teacher logits found. Returning 0.0 for global eigenvalue.")
        return 0.0
    
    matrix = np.array(all_logits)
    logger.info(f"Constructed global teacher score matrix of shape: {matrix.shape}")
    
    # Compute covariance matrix (4x4)
    # np.cov expects variables as rows, observations as columns by default?
    # Actually np.cov(m) where m is (N, M) treats rows as variables.
    # We want covariance between the 4 dimensions.
    # So we pass matrix.T to np.cov so that each row is a dimension.
    try:
        cov_matrix = np.cov(matrix.T)
    except Exception as e:
        logger.error(f"Failed to compute covariance matrix: {e}")
        return 0.0
    
    logger.info(f"Global Covariance Matrix:\n{cov_matrix}")
    
    # Calculate eigenvalues
    eigenvalues = np.linalg.eigvals(cov_matrix)
    
    # Get the dominant (largest) eigenvalue (real part, as covariance matrices are symmetric/Hermitian)
    # Ensure we take the real part if there's tiny imaginary noise
    dominant_eigenvalue = float(np.max(np.real(eigenvalues)))
    
    # Validation: Ensure finite and non-NaN
    if not np.isfinite(dominant_eigenvalue):
        logger.error("Dominant eigenvalue is not finite. Returning 0.0.")
        return 0.0
    
    logger.info(f"Dominant Eigenvalue (Global Entanglement Score): {dominant_eigenvalue}")
    return dominant_eigenvalue

def calculate_dimensional_fidelity_loss(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate MAE between student scalar and human annotation for the primary dimension.
    """
    logger = logging.getLogger(__name__)
    logger.info("Calculating dimensional fidelity loss (T024)...")
    
    results = []
    for _, row in df.iterrows():
        student_scalar = row.get('student_scalar')
        human_annotations = row.get('human_annotations', {})
        primary_dim = row.get('primary_dimension', 'Alignment')
        
        if student_scalar is None or primary_dim not in human_annotations:
            # Missing data handling
            results.append({"sample_id": row.get('sample_id', 0), "fidelity_loss": None})
            continue
        
        human_score = human_annotations[primary_dim]
        if human_score is None:
            results.append({"sample_id": row.get('sample_id', 0), "fidelity_loss": None})
            continue
        
        mae = abs(float(student_scalar) - float(human_score))
        results.append({"sample_id": row.get('sample_id', 0), "fidelity_loss": mae})
    
    return pd.DataFrame(results)

def save_features_to_json(features_df: pd.DataFrame, global_eigenvalue: float, output_path: str):
    """
    Merge per-sample stats with global eigenvalue and save to JSON.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Saving features to {output_path}")
    
    # Add global eigenvalue to every row
    features_df['dominant_eigenvalue'] = global_eigenvalue
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert to list of dicts and save
    # Handle potential NaN in fidelity_loss by converting to null or specific value
    features_df = features_df.where(pd.notnull(features_df), None)
    
    with open(output_path, 'w') as f:
        json.dump(features_df.to_dict(orient='records'), f, indent=2)
    
    logger.info(f"Features saved successfully to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Feature Engineering Pipeline")
    parser.add_argument("--input", type=str, required=True, help="Path to aligned data (CSV/JSON)")
    parser.add_argument("--output", type=str, required=True, help="Path to output features JSON")
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()
    
    try:
        # 1. Load Data
        df = load_aligned_data(args.input)
        
        # 2. Calculate Per-Sample Stats (T022a)
        per_sample_stats = calculate_per_sample_stats(df)
        
        # 3. Calculate Global Eigenvalue (T022b)
        global_eigenvalue = calculate_global_entanglement_score(df)
        
        # 4. Calculate Fidelity Loss (T024)
        fidelity_loss_df = calculate_dimensional_fidelity_loss(df)
        
        # 5. Merge Data
        # Merge per_sample_stats and fidelity_loss_df on sample_id
        merged = pd.merge(per_sample_stats, fidelity_loss_df, on='sample_id', how='left')
        
        # 6. Save Results
        save_features_to_json(merged, global_eigenvalue, args.output)
        
        logger.info("Feature engineering completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()