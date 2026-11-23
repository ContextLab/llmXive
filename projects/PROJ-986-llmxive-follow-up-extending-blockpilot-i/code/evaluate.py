import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from scipy import stats

from utils.data_loader import load_dataset_streaming
from utils.metrics import calculate_correlation, calculate_pcc, calculate_scc
from utils.join_utils import load_jsonl, save_jsonl, join_ground_truth_and_features, join_uncertainty_metrics
from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_training_data(features_path: str, ground_truth_path: str) -> List[Dict[str, Any]]:
    """Load and join features and ground truth data."""
    try:
        features = load_jsonl(features_path)
        ground_truth = load_jsonl(ground_truth_path)
        
        if not features or not ground_truth:
            logger.warning(f"One of the input files is empty: features={features_path}, gt={ground_truth_path}")
            return []
        
        joined_data = join_ground_truth_and_features(features, ground_truth)
        logger.info(f"Joined {len(joined_data)} samples for training.")
        return joined_data
    except Exception as e:
        logger.error(f"Error loading training data: {e}")
        return []

def preprocess_features(data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
    """Extract features and target from joined data."""
    if not data:
        return np.array([]), np.array([])
    
    X = []
    y = []
    for item in data:
        # Ensure we have the required fields
        if 'features' in item and 'optimal_block_size' in item:
            feat_vec = item['features']
            # Flatten if necessary (assuming list of floats)
            if isinstance(feat_vec, list):
                X.append(feat_vec)
            else:
                X.append([feat_vec]) # Handle single feature case if any
            y.append(item['optimal_block_size'])
    
    if not X:
        return np.array([]), np.array([])
    
    return np.array(X), np.array(y)

def load_uncertainty_metrics(path: str) -> Dict[str, Dict[str, Any]]:
    """Load uncertainty metrics from JSONL file indexed by sample_id."""
    try:
        records = load_jsonl(path)
        if not records:
            logger.warning(f"No uncertainty metrics found at {path}")
            return {}
        
        # Index by sample_id for quick lookup
        return {r.get('sample_id'): r for r in records if r.get('sample_id')}
    except FileNotFoundError:
        logger.error(f"Uncertainty metrics file not found: {path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading uncertainty metrics: {e}")
        return {}

def calculate_uncertainty_correlation(
    joined_data: List[Dict[str, Any]],
    uncertainty_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Calculate Pearson and Spearman correlations between predicted optimal block size
    and uncertainty metrics (perplexity, output_entropy).
    
    This function implements the core requirement of T046.
    """
    logger.info(f"Starting uncertainty correlation analysis. Output: {output_path}")
    
    # Load uncertainty metrics
    uncertainty_map = load_uncertainty_metrics(uncertainty_path)
    if not uncertainty_map:
        error_result = {
            "timestamp": datetime.now().isoformat(),
            "sample_count": 0,
            "correlations": {},
            "summary": "Correlation analysis failed: No uncertainty data found.",
            "error": f"File not found or empty: {uncertainty_path}"
        }
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(error_result, f, indent=2)
        return error_result

    # Extract matched data
    perplexity_scores = []
    entropy_scores = []
    block_sizes = []
    matched_ids = []

    for item in joined_data:
        sample_id = item.get('sample_id')
        if not sample_id or sample_id not in uncertainty_map:
            continue
        
        u_data = uncertainty_map[sample_id]
        opt_bs = item.get('optimal_block_size')
        
        if opt_bs is None:
            continue

        p_val = u_data.get('perplexity')
        e_val = u_data.get('output_entropy')

        if p_val is not None and e_val is not None and opt_bs is not None:
            # Filter NaN/Inf just in case
            if np.isfinite(p_val) and np.isfinite(e_val) and np.isfinite(opt_bs):
                perplexity_scores.append(p_val)
                entropy_scores.append(e_val)
                block_sizes.append(opt_bs)
                matched_ids.append(sample_id)

    if len(block_sizes) == 0:
        error_result = {
            "timestamp": datetime.now().isoformat(),
            "sample_count": 0,
            "correlations": {},
            "summary": "Correlation analysis failed: No matched samples with valid uncertainty metrics.",
            "error": "No valid data points after joining."
        }
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(error_result, f, indent=2)
        return error_result

    logger.info(f"Correlation analysis on {len(block_sizes)} matched samples.")

    # Calculate correlations
    # Perplexity
    p_pearson, p_pval = stats.pearsonr(block_sizes, perplexity_scores)
    p_spear, p_sval = stats.spearmanr(block_sizes, perplexity_scores)
    
    # Output Entropy
    e_pearson, e_pval = stats.pearsonr(block_sizes, entropy_scores)
    e_spear, e_sval = stats.spearmanr(block_sizes, entropy_scores)

    result = {
        "timestamp": datetime.now().isoformat(),
        "sample_count": len(block_sizes),
        "correlations": {
            "perplexity": {
                "pearson": {
                    "coefficient": float(p_pearson),
                    "p_value": float(p_pval),
                    "significant": bool(p_pval < 0.05)
                },
                "spearman": {
                    "coefficient": float(p_spear),
                    "p_value": float(p_sval),
                    "significant": bool(p_sval < 0.05)
                }
            },
            "output_entropy": {
                "pearson": {
                    "coefficient": float(e_pearson),
                    "p_value": float(e_pval),
                    "significant": bool(e_pval < 0.05)
                },
                "spearman": {
                    "coefficient": float(e_spear),
                    "p_value": float(e_sval),
                    "significant": bool(e_sval < 0.05)
                }
            }
        },
        "summary": f"Correlation analysis completed between predicted block size and uncertainty metrics. "
                   f"Perplexity Pearson: {p_pearson:.4f} (p={p_pval:.4f}), "
                   f"Entropy Pearson: {e_pearson:.4f} (p={e_pval:.4f}).",
        "error": None
    }

    # Write result
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Correlation report written to {output_path}")
    return result

def run_cross_architecture_validation(train_arch: str, test_arch: str, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Placeholder for cross-architecture validation logic.
    In a full implementation, this would train on one architecture's data and test on another.
    """
    logger.info(f"Cross-architecture validation: Train {train_arch} -> Test {test_arch}")
    # Implementation would go here
    return {"status": "skipped", "reason": "Implementation pending full data split"}

def get_feature_importance(model, feature_names: List[str]) -> Dict[str, float]:
    """Extract feature importance from a trained model."""
    # Placeholder for importance extraction logic
    return {}

def evaluate_and_report(
    features_path: str,
    ground_truth_path: str,
    uncertainty_path: str,
    output_report_path: str
) -> Dict[str, Any]:
    """
    Main entry point for evaluation and correlation reporting.
    Orchestrates loading, joining, and correlation calculation.
    """
    logger.info("Starting evaluation and correlation reporting.")
    
    # 1. Load and Join Data (Training Set)
    joined_data = load_training_data(features_path, ground_truth_path)
    
    if not joined_data:
        logger.error("No joined training data available. Cannot proceed with correlation.")
        return {"error": "No training data"}

    # 2. Calculate Uncertainty Correlation (T046 Core)
    correlation_result = calculate_uncertainty_correlation(
        joined_data, 
        uncertainty_path, 
        output_report_path
    )

    # 3. Additional evaluations could go here (model training, etc.)
    
    return correlation_result

def main():
    """CLI entry point for the evaluation script."""
    config = load_config()
    
    # Default paths from config or constants
    features_path = config.get('paths', {}).get('features', 'data/processed/features.jsonl')
    ground_truth_path = config.get('paths', {}).get('ground_truth', 'data/processed/ground_truth.jsonl')
    uncertainty_path = config.get('paths', {}).get('uncertainty_metrics', 'data/processed/uncertainty_metrics.jsonl')
    output_report_path = config.get('paths', {}).get('correlation_report', 'data/processed/correlation_report.json')

    # Ensure paths exist if they are expected
    if not os.path.exists(ground_truth_path) or not os.path.exists(features_path):
        logger.error("Required input files (ground_truth.jsonl, features.jsonl) not found.")
        return

    result = evaluate_and_report(
        features_path=features_path,
        ground_truth_path=ground_truth_path,
        uncertainty_path=uncertainty_path,
        output_report_path=output_report_path
    )

    if result.get("error"):
        logger.error(f"Evaluation failed: {result['error']}")
        return 1
    
    logger.info("Evaluation completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
