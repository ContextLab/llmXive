"""
Pearson Correlation Analysis for Topological Features vs Thermal Conductivity.

Implements FR-005: Primary statistical analysis correlating feature importance (SHAP values)
with global thermal conductivity.
"""
import json
import logging
import pickle
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats

# Import configuration utilities
from config import get_config, get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_feature_importance_data(shap_path: Path) -> Tuple[np.ndarray, List[str]]:
    """
    Load SHAP values from the feature importance output.

    Args:
        shap_path: Path to the shap_values.npy file.

    Returns:
        Tuple of (shap_values array, feature_names list).
    """
    if not shap_path.exists():
        raise FileNotFoundError(f"Feature importance file not found: {shap_path}")

    logger.info(f"Loading feature importance data from {shap_path}")
    
    # Load numpy array
    shap_values = np.load(shap_path)
    
    # We expect shape [N_samples, N_features]
    if shap_values.ndim != 2:
        raise ValueError(f"Expected 2D array [N_samples, N_features], got shape {shap_values.shape}")

    logger.info(f"Loaded SHAP values with shape: {shap_values.shape}")
    
    # Feature names are typically stored alongside or derived from config
    # For this implementation, we assume standard topological features
    # If the .npy file contains a structured array or metadata, we'd load that too.
    # Here we infer feature count.
    n_features = shap_values.shape[1]
    feature_names = [f"feature_{i}" for i in range(n_features)]
    
    # If a corresponding metadata file exists (e.g., feature_names.json), load it
    meta_path = shap_path.with_suffix('.json')
    if meta_path.exists():
        with open(meta_path, 'r') as f:
            meta = json.load(f)
            if 'feature_names' in meta:
                feature_names = meta['feature_names']
                logger.info(f"Loaded feature names from {meta_path}")

    return shap_values, feature_names

def load_thermal_conductivity_data(conductivity_dir: Path) -> Dict[str, float]:
    """
    Load thermal conductivity values from the processed conductivities directory.
    Reads all JSON files in the directory containing conductivity data.

    Args:
        conductivity_dir: Path to the directory containing thermal sample files.

    Returns:
        Dictionary mapping sample_id to conductivity value.
    """
    logger.info(f"Loading thermal conductivity data from {conductivity_dir}")
    
    conductivity_map = {}
    
    if not conductivity_dir.exists():
        raise FileNotFoundError(f"Conductivity directory not found: {conductivity_dir}")

    # Look for JSON files (thermal_sample.json format)
    for file_path in conductivity_dir.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract sample ID and conductivity
            sample_id = data.get('graph_id') or data.get('sample_id')
            conductivity = data.get('conductivity')
            
            if sample_id and conductivity is not None:
                conductivity_map[sample_id] = float(conductivity)
                logger.debug(f"Loaded sample {sample_id}: conductivity = {conductivity}")
            else:
                logger.warning(f"Skipping {file_path}: missing sample_id or conductivity")
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON in {file_path}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

    if not conductivity_map:
        raise ValueError("No valid thermal conductivity data found in the specified directory.")

    logger.info(f"Loaded {len(conductivity_map)} thermal conductivity samples")
    return conductivity_map

def align_data(
    shap_values: np.ndarray, 
    feature_names: List[str], 
    conductivity_map: Dict[str, float],
    sample_ids: List[str]
) -> Tuple[np.ndarray, np.ndarray, List[int]]:
    """
    Align SHAP values and conductivity data based on sample IDs.

    Args:
        shap_values: 2D array of shape [N_samples, N_features].
        feature_names: List of feature names.
        conductivity_map: Dict mapping sample_id to conductivity.
        sample_ids: List of sample IDs corresponding to the rows in shap_values.

    Returns:
        Tuple of (aligned_shap, aligned_conductivity, valid_indices).
    """
    valid_indices = []
    aligned_shap = []
    aligned_conductivity = []

    for i, sample_id in enumerate(sample_ids):
        if sample_id in conductivity_map:
            valid_indices.append(i)
            aligned_shap.append(shap_values[i])
            aligned_conductivity.append(conductivity_map[sample_id])
        else:
            logger.warning(f"Sample {sample_id} found in SHAP data but missing in conductivity data. Skipping.")

    if not valid_indices:
        raise ValueError("No overlapping samples found between SHAP data and conductivity data.")

    aligned_shap = np.array(aligned_shap)
    aligned_conductivity = np.array(aligned_conductivity)

    logger.info(f"Aligned data: {len(valid_indices)} samples used for correlation.")
    return aligned_shap, aligned_conductivity, valid_indices

def compute_pearson_correlation(
    shap_values: np.ndarray, 
    conductivity: np.ndarray
) -> Dict[str, Dict[str, float]]:
    """
    Compute Pearson correlation coefficient and p-value for each feature against conductivity.

    Args:
        shap_values: 2D array [N_samples, N_features].
        conductivity: 1D array [N_samples].

    Returns:
        Dictionary mapping feature index to {r, p_value}.
    """
    n_samples, n_features = shap_values.shape
    results = {}

    logger.info(f"Computing Pearson correlation for {n_features} features across {n_samples} samples.")

    for i in range(n_features):
        feature_shap = shap_values[:, i]
        
        # Handle constant features (zero variance)
        if np.std(feature_shap) < 1e-10:
            results[i] = {'r': 0.0, 'p_value': 1.0, 'n': n_samples}
            logger.debug(f"Feature {i} is constant. Skipping correlation.")
            continue

        try:
            r, p_value = stats.pearsonr(feature_shap, conductivity)
            results[i] = {'r': float(r), 'p_value': float(p_value), 'n': n_samples}
        except Exception as e:
            logger.error(f"Error computing correlation for feature {i}: {e}")
            results[i] = {'r': float('nan'), 'p_value': float('nan'), 'n': n_samples}

    return results

def generate_correlation_report(
    correlation_results: Dict[int, Dict[str, float]], 
    feature_names: List[str],
    n_samples: int
) -> Dict[str, Any]:
    """
    Generate a summary report of the correlation analysis.

    Args:
        correlation_results: Dict of correlation stats per feature.
        feature_names: List of feature names.
        n_samples: Total number of samples used.

    Returns:
        Dictionary containing the full report.
    """
    report = {
        'method': 'pearson',
        'n_samples': n_samples,
        'results': []
    }

    # Sort by absolute correlation magnitude (descending)
    sorted_features = sorted(
        correlation_results.items(),
        key=lambda x: abs(x[1]['r']),
        reverse=True
    )

    for feat_idx, stats_dict in sorted_features:
        feat_name = feature_names[feat_idx] if feat_idx < len(feature_names) else f"feature_{feat_idx}"
        report['results'].append({
            'feature': feat_name,
            'feature_index': feat_idx,
            'r': stats_dict['r'],
            'p_value': stats_dict['p_value'],
            'n_samples': stats_dict['n']
        })

    return report

def save_results(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the correlation report to a JSON file.

    Args:
        report: The correlation report dictionary.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Correlation results saved to {output_path}")

def main() -> int:
    """
    Main entry point for the Pearson correlation analysis pipeline.
    """
    try:
        config = get_config()
        paths = get_paths()
        
        # Define paths based on config
        shap_path = paths['data_processed_model_outputs'] / 'shap_values.npy'
        conductivity_dir = paths['data_processed_conductivities']
        output_path = paths['data_processed_model_outputs'] / 'correlation_pearson.json'

        logger.info("Starting Pearson Correlation Analysis (T033a)")

        # 1. Load Feature Importance (SHAP)
        shap_values, feature_names = load_feature_importance_data(shap_path)

        # 2. Load Conductivity Data
        conductivity_map = load_thermal_conductivity_data(conductivity_dir)

        # 3. Align Data
        # We need the sample IDs that correspond to the SHAP rows.
        # Assuming the SHAP values were generated in the same order as the thermal samples.
        # If sample IDs are not explicitly stored in the SHAP file, we rely on the order
        # of the thermal samples directory listing or a manifest.
        # For robustness, we check for a manifest file.
        manifest_path = paths['data_processed_model_outputs'] / 'shap_manifest.json'
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            sample_ids = manifest.get('sample_ids', [])
        else:
            # Fallback: Assume order matches conductivity map keys if sorted consistently
            # This is risky. Better to enforce a manifest in T032.
            # We will sort conductivity_map keys to ensure deterministic order if no manifest exists.
            logger.warning("No SHAP manifest found. Assuming order matches sorted conductivity sample IDs.")
            sample_ids = sorted(conductivity_map.keys())[:shap_values.shape[0]]

        aligned_shap, aligned_conductivity, valid_indices = align_data(
            shap_values, feature_names, conductivity_map, sample_ids
        )

        # 4. Compute Correlations
        correlation_results = compute_pearson_correlation(aligned_shap, aligned_conductivity)

        # 5. Generate Report
        report = generate_correlation_report(correlation_results, feature_names, len(valid_indices))

        # 6. Save Results
        save_results(report, output_path)

        logger.info("Pearson Correlation Analysis completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
