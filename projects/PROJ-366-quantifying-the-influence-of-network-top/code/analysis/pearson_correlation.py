"""
T033a: Implement Pearson correlation analysis between feature importance and global thermal conductivity.

This module computes the Pearson correlation coefficient and p-value between
the extracted feature importance scores (from the GNN model) and the global
thermal conductivity values for the available samples.

Output: data/processed/model_outputs/correlation_pearson.json
"""
import json
import logging
import pickle
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats

# Import shared config utilities
from config import get_config, get_paths

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_feature_importance_data(feature_importance_path: Path) -> Dict[str, List[float]]:
    """
    Load feature importance data from the trained model output.
    
    Args:
        feature_importance_path: Path to the feature importance JSON file.
        
    Returns:
        Dictionary mapping feature names to lists of importance scores.
    """
    if not feature_importance_path.exists():
        raise FileNotFoundError(f"Feature importance file not found: {feature_importance_path}")
    
    with open(feature_importance_path, 'r') as f:
        data = json.load(f)
    
    return data

def load_thermal_conductivity_data(conductivity_dir: Path) -> Dict[str, float]:
    """
    Load thermal conductivity values from processed thermal samples.
    
    Args:
        conductivity_dir: Directory containing thermal sample pickle files.
        
    Returns:
        Dictionary mapping sample IDs to thermal conductivity values (W/mK).
    """
    conductivity_data = {}
    
    if not conductivity_dir.exists():
        raise FileNotFoundError(f"Conductivity directory not found: {conductivity_dir}")
    
    for sample_file in conductivity_dir.glob("*.pkl"):
        try:
            with open(sample_file, 'rb') as f:
                sample_data = pickle.load(f)
            
            sample_id = sample_data.get('id') or sample_file.stem
            conductivity = sample_data.get('conductivity')
            
            if conductivity is not None:
                conductivity_data[sample_id] = float(conductivity)
            else:
                logger.warning(f"Sample {sample_id} missing conductivity value, skipping.")
                
        except Exception as e:
            logger.error(f"Error loading sample {sample_file}: {e}")
            continue
    
    return conductivity_data

def align_data(
    feature_importance: Dict[str, List[float]], 
    conductivity_data: Dict[str, float]
) -> Tuple[List[str], List[List[float]], List[float]]:
    """
    Align feature importance and conductivity data by sample ID.
    
    Args:
        feature_importance: Feature importance data by sample ID.
        conductivity_data: Conductivity data by sample ID.
        
    Returns:
        Tuple of (sample_ids, feature_matrix, conductivity_values).
    """
    common_ids = sorted(set(feature_importance.keys()) & set(conductivity_data.keys()))
    
    if not common_ids:
        raise ValueError("No common samples found between feature importance and conductivity data.")
    
    feature_matrix = []
    conductivity_values = []
    
    for sample_id in common_ids:
        features = feature_importance[sample_id]
        cond_val = conductivity_data[sample_id]
        
        # Ensure feature list is uniform length
        if len(features) > 0:
            feature_matrix.append(features)
            conductivity_values.append(cond_val)
        else:
            logger.warning(f"Sample {sample_id} has empty feature importance, skipping.")
    
    return common_ids, feature_matrix, conductivity_values

def compute_pearson_correlation(
    feature_matrix: List[List[float]], 
    conductivity_values: List[float]
) -> Dict[str, Dict[str, float]]:
    """
    Compute Pearson correlation between each feature and conductivity.
    
    Args:
        feature_matrix: List of feature vectors (one per sample).
        conductivity_values: List of conductivity values (one per sample).
        
    Returns:
        Dictionary mapping feature indices to correlation results (r, p-value).
    """
    results = {}
    n_features = len(feature_matrix[0]) if feature_matrix else 0
    
    for i in range(n_features):
        feature_values = [row[i] for row in feature_matrix]
        
        if len(feature_values) < 2:
            logger.warning(f"Feature {i} has insufficient data for correlation.")
            results[f"feature_{i}"] = {"r": np.nan, "p_value": np.nan}
            continue
        
        try:
            r, p_value = stats.pearsonr(feature_values, conductivity_values)
            results[f"feature_{i}"] = {
                "r": float(r),
                "p_value": float(p_value)
            }
        except Exception as e:
            logger.error(f"Error computing correlation for feature {i}: {e}")
            results[f"feature_{i}"] = {"r": np.nan, "p_value": np.nan}
    
    return results

def generate_correlation_report(
    sample_ids: List[str],
    correlation_results: Dict[str, Dict[str, float]],
    feature_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive correlation report.
    
    Args:
        sample_ids: List of aligned sample IDs.
        correlation_results: Correlation results per feature.
        feature_names: Optional list of feature names for better labeling.
        
    Returns:
        Dictionary containing the full correlation report.
    """
    report = {
        "analysis_type": "Pearson Correlation",
        "description": "Correlation between feature importance and thermal conductivity",
        "sample_count": len(sample_ids),
        "sample_ids": sample_ids,
        "features_analyzed": len(correlation_results),
        "results": correlation_results
    }
    
    if feature_names:
        report["feature_names"] = feature_names
    
    # Add summary statistics
    r_values = [v["r"] for v in correlation_results.values() if not np.isnan(v["r"])]
    p_values = [v["p_value"] for v in correlation_results.values() if not np.isnan(v["p_value"])]
    
    if r_values:
        report["summary"] = {
            "mean_r": float(np.mean(r_values)),
            "min_r": float(np.min(r_values)),
            "max_r": float(np.max(r_values)),
            "significant_correlations_count": sum(1 for p in p_values if p < 0.05)
        }
    
    return report

def main():
    """Main entry point for Pearson correlation analysis."""
    logger.info("Starting Pearson correlation analysis (T033a).")
    
    config = get_config()
    paths = get_paths()
    
    # Define input paths
    feature_importance_path = paths["model_outputs"] / "feature_importance.json"
    conductivity_dir = paths["conductivities"]
    output_dir = paths["model_outputs"]
    output_file = output_dir / "correlation_pearson.json"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        logger.info(f"Loading feature importance from {feature_importance_path}")
        feature_importance_data = load_feature_importance_data(feature_importance_path)
        
        logger.info(f"Loading conductivity data from {conductivity_dir}")
        conductivity_data = load_thermal_conductivity_data(conductivity_dir)
        
        # Align data
        logger.info("Aligning feature and conductivity data.")
        sample_ids, feature_matrix, conductivity_values = align_data(
            feature_importance_data, 
            conductivity_data
        )
        
        if len(sample_ids) < 2:
            logger.error("Insufficient samples for correlation analysis (need >= 2).")
            sys.exit(1)
        
        logger.info(f"Aligned {len(sample_ids)} samples for analysis.")
        
        # Compute correlations
        logger.info("Computing Pearson correlations.")
        correlation_results = compute_pearson_correlation(feature_matrix, conductivity_values)
        
        # Generate report
        report = generate_correlation_report(sample_ids, correlation_results)
        
        # Save results
        logger.info(f"Saving results to {output_file}")
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("Pearson correlation analysis completed successfully.")
        print(f"Results written to: {output_file}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data alignment error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
