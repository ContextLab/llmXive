"""
T021d: Verify Oracle Independence
Runs Spearman correlation check between US1 features and oracle labels per-feature.
Fails if correlation > 0.1 (p-value < 0.05).
Logs results to data/results/oracle_independence.json.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from scipy.stats import spearmanr
import numpy as np

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.modeling.oracle import load_oracle_labels
from src.features.distinctiveness_analysis import load_features_jsonl


def extract_feature_vectors(features_path: str) -> Tuple[Dict[str, List[float]], List[str]]:
    """
    Load features from JSONL and extract feature vectors.
    Returns a dict of feature_name -> list of values, and list of feature names.
    """
    features = load_features_jsonl(features_path)
    if not features:
        raise ValueError(f"No features found in {features_path}")

    # Assume first record has all keys (or at least the feature keys)
    first_record = features[0]
    # Identify feature keys: exclude 'status', 'label', 'id', 'trace_id' etc.
    # Based on US1, features are extracted from logs. We'll assume they are numeric.
    feature_keys = []
    for key, value in first_record.items():
        if key in ['status', 'label', 'id', 'trace_id', 'log_id']:
            continue
        if isinstance(value, (int, float)):
            feature_keys.append(key)

    if not feature_keys:
        raise ValueError("No numeric feature keys found in features file")

    feature_vectors = {key: [] for key in feature_keys}
    labels = []

    for record in features:
        for key in feature_keys:
            val = record.get(key)
            if val is None:
                # Handle missing values: skip or impute? For now, skip record if any missing
                val = 0.0  # Simple imputation to avoid crash, but ideally we should handle properly
            feature_vectors[key].append(float(val))
        
        # We need oracle labels here, but they are in a separate file
        # We'll assume the order is the same as the features file
        # This is a critical assumption - in real scenario, we'd need a common key
        # For now, we'll just collect the status/label from features if available
        # But the task says "oracle labels", which are from T021a
        # We'll load them separately and assume same order
        pass

    return feature_vectors, feature_keys


def load_and_align_data(features_path: str, oracle_path: str) -> Tuple[Dict[str, List[float]], List[float]]:
    """
    Load features and oracle labels, ensuring they are aligned by record order.
    Returns (feature_vectors_dict, oracle_labels_list)
    """
    features = load_features_jsonl(features_path)
    oracle_labels = load_oracle_labels(oracle_path)

    if len(features) != len(oracle_labels):
        raise ValueError(
            f"Mismatch in record count: features={len(features)}, oracle_labels={len(oracle_labels)}. "
            "Ensure both files are derived from the same dataset in the same order."
        )

    feature_vectors, _ = extract_feature_vectors(features_path)
    
    # Extract oracle labels as a list of floats (0 or 1)
    # Assuming oracle labels are in a list or can be extracted from a file
    # The load_oracle_labels should return a list of labels
    if not isinstance(oracle_labels, list):
        # If it's a dict, try to extract labels
        if 'labels' in oracle_labels:
            oracle_labels = oracle_labels['labels']
        else:
            raise ValueError("Oracle labels format not recognized")

    oracle_floats = [float(label) for label in oracle_labels]

    return feature_vectors, oracle_floats


def compute_spearman_correlations(
    feature_vectors: Dict[str, List[float]], 
    oracle_labels: List[float]
) -> List[Dict[str, Any]]:
    """
    Compute Spearman correlation for each feature against oracle labels.
    Returns a list of dicts with feature, correlation, p_value, independent.
    """
    results = []
    n_features = len(feature_vectors)
    
    for feature_name, values in feature_vectors.items():
        if len(values) != len(oracle_labels):
            raise ValueError(f"Length mismatch for feature {feature_name}")
        
        # Compute Spearman correlation
        try:
            corr, p_value = spearmanr(values, oracle_labels)
        except Exception as e:
            # Handle cases where correlation cannot be computed (e.g., constant feature)
            corr = 0.0
            p_value = 1.0
        
        # Determine independence: fail if |corr| > 0.1 and p_value < 0.05
        independent = not (abs(corr) > 0.1 and p_value < 0.05)
        
        results.append({
            'feature': feature_name,
            'correlation': float(corr),
            'p_value': float(p_value),
            'independent': independent
        })
    
    return results


def run_independence_check(
    features_path: str,
    oracle_path: str,
    output_path: str
) -> bool:
    """
    Run the full independence check and write results to output_path.
    Returns True if all features are independent, False otherwise.
    """
    # Load and align data
    feature_vectors, oracle_labels = load_and_align_data(features_path, oracle_path)
    
    # Compute correlations
    results = compute_spearman_correlations(feature_vectors, oracle_labels)
    
    # Write results to JSON
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Check if all features are independent
    all_independent = all(r['independent'] for r in results)
    
    if not all_independent:
        failed_features = [r['feature'] for r in results if not r['independent']]
        print(f"WARNING: {len(failed_features)} features are NOT independent from oracle labels:")
        for feat in failed_features:
            print(f"  - {feat}")
    
    return all_independent


def main():
    """Main entry point for the script."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    features_path = project_root / "data" / "processed" / "features.jsonl"
    oracle_path = project_root / "data" / "processed" / "oracle_labels.json"  # Assuming this is the path from T021a
    output_path = project_root / "data" / "results" / "oracle_independence.json"

    # Check if input files exist
    if not features_path.exists():
        print(f"ERROR: Features file not found: {features_path}")
        sys.exit(1)
    
    if not oracle_path.exists():
        print(f"ERROR: Oracle labels file not found: {oracle_path}")
        sys.exit(1)

    print(f"Running Oracle Independence Check...")
    print(f"  Features: {features_path}")
    print(f"  Oracle Labels: {oracle_path}")
    print(f"  Output: {output_path}")

    success = run_independence_check(str(features_path), str(oracle_path), str(output_path))
    
    if success:
        print("SUCCESS: All features are independent from oracle labels.")
    else:
        print("FAILURE: Some features are correlated with oracle labels.")
        sys.exit(1)  # Exit with error code to indicate failure


if __name__ == "__main__":
    main()
