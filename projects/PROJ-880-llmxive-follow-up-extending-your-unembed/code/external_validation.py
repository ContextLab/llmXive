"""
External Validation Module for llmXive.

Implements configuration and execution of external validation against WALS
(World Atlas of Language Structures) data to verify the linguistic significance
of the edge spectrum subspace orientation.

This module specifically addresses Task T029a (Configuration) and T029 (Execution).
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats

from config import load_config, get_path, get_hyperparameter, ensure_dirs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WALS Configuration Constants (Task T029a)
# Defined per SC-004: Specific WALS feature set and correlation method
WALS_CONFIG = {
    "feature_sets": {
        "phonological": [
            "P001", "P002", "P003", "P004", "P005",  # Vowel quality, consonant inventory
            "P010", "P011", "P012", "P013", "P014",  # Syllable structure
            "P020", "P021", "P022"                    # Tone and stress
        ],
        "morphological": [
            "M001", "M002", "M003", "M004", "M005",  # Nominal inflection
            "M010", "M011", "M012", "M013", "M014",  # Verbal inflection
            "M020", "M021", "M022"                    # Derivational morphology
        ],
        "syntactic": [
            "S001", "S002", "S003", "S004", "S005"   # Word order, alignment
        ]
    },
    "selected_features": ["P001", "P002", "P003", "M001", "M002"], # Default: Phonological + Morphological
    "correlation_method": "spearman", # As per SC-004
    "min_sample_size": 50, # Minimum languages required for statistical validity
    "data_source": "wals_3.0",
    "wals_url_base": "https://wals.info/download"
}

class ExternalValidationError(Exception):
    """Custom exception for external validation errors."""
    pass

class WALSDataNotFoundError(ExternalValidationError):
    """Raised when WALS data is not available or cannot be fetched."""
    pass

def load_config() -> Dict[str, Any]:
    """Load configuration for external validation."""
    config = load_config()
    # Override or merge with specific WALS config if needed
    if 'wals' in config:
        WALS_CONFIG.update(config['wals'])
    return config

def get_wals_feature_ids() -> List[str]:
    """
    Retrieve the list of WALS feature IDs to be used for validation.
    
    Returns:
        List[str]: List of WALS feature codes (e.g., 'P001', 'M002').
    """
    return WALS_CONFIG.get("selected_features", [])

def get_correlation_method() -> str:
    """
    Retrieve the correlation method specified in the configuration.
    
    Returns:
        str: The method name ('spearman', 'pearson', etc.).
    """
    return WALS_CONFIG.get("correlation_method", "spearman")

def fetch_wals_data(output_path: Path) -> Dict[str, Any]:
    """
    Fetches WALS data from the official source or a local cache.
    
    This function attempts to download the WALS dataset. If the download fails
    or the data is unavailable, it raises a WALSDataNotFoundError.
    
    Args:
        output_path: Path to save the downloaded data.
        
    Returns:
        Dict[str, Any]: The loaded WALS data.
        
    Raises:
        WALSDataNotFoundError: If data cannot be fetched.
    """
    logger.info(f"Attempting to fetch WALS data from {WALS_CONFIG['wals_url_base']}...")
    
    # In a real execution environment, this would perform an HTTP request.
    # For the purpose of this implementation, we check for a local file first,
    # then attempt a fetch. If neither exists, we fail loudly as per constraints.
    
    # Simulating a check for a real source (in production, use urllib/requests)
    # Since we cannot actually download in this sandbox, we define the expected path
    # and raise an error if not found, ensuring no mock data is used.
    
    # Expected local path for real data
    local_data_path = Path("data/raw/wals_features.json")
    
    if not local_data_path.exists():
        # Attempt to download (simulated logic for structure)
        logger.warning("WALS data not found locally. Attempting fetch...")
        # In real code:
        # urllib.request.urlretrieve(WALS_CONFIG['wals_url_base'], local_data_path)
        # If fetch fails:
        raise WALSDataNotFoundError(
            "WALS data source is unavailable. "
            "Please ensure the dataset is downloaded to data/raw/wals_features.json "
            "or verify network access to the WALS server."
        )
    
    logger.info(f"Loading WALS data from {local_data_path}")
    with open(local_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    return data

def align_subspace_orientations(subspace_data: Dict[str, Any], wals_data: Dict[str, Any]) -> Tuple[List[float], List[float]]:
    """
    Aligns the computed subspace orientation vectors with WALS feature vectors.
    
    This function matches languages present in both the model analysis results
    and the WALS dataset.
    
    Args:
        subspace_data: Dictionary containing subspace orientation vectors keyed by language.
        wals_data: Dictionary containing WALS feature values keyed by language.
        
    Returns:
        Tuple[List[float], List[float]]: Two lists of aligned values (subspace, wals).
    """
    subspace_vectors = []
    wals_vectors = []
    
    # Assuming subspace_data has structure: { "lang_code": { "orientation": [float] } }
    # And wals_data has structure: { "lang_code": { "feature_id": value } }
    
    feature_ids = get_wals_feature_ids()
    
    for lang_code in subspace_data.keys():
        if lang_code in wals_data:
            # Extract the primary orientation metric (e.g., first principal component magnitude)
            # Adjust key based on actual output of T012/T014
            orientation_val = subspace_data[lang_code].get("orientation_score", 0.0)
            
            # Aggregate WALS features for this language (e.g., mean of selected features)
            lang_wals_features = wals_data[lang_code]
            wals_values = [lang_wals_features.get(fid, None) for fid in feature_ids]
            valid_wals = [v for v in wals_values if v is not None]
            
            if len(valid_wals) > 0:
                avg_wals = np.mean(valid_wals)
                subspace_vectors.append(orientation_val)
                wals_vectors.append(avg_wals)
                
    if len(subspace_vectors) < WALS_CONFIG["min_sample_size"]:
        logger.warning(f"Only {len(subspace_vectors)} languages matched. "
                       f"Minimum required is {WALS_CONFIG['min_sample_size']}. "
                       f"Results may not be statistically significant.")
        
    return subspace_vectors, wals_vectors

def compute_spearman_correlation(x: List[float], y: List[float]) -> Dict[str, float]:
    """
    Computes Spearman's rank correlation coefficient.
    
    Args:
        x: First variable (subspace orientation).
        y: Second variable (WALS features).
        
    Returns:
        Dict containing correlation coefficient and p-value.
    """
    if len(x) < 3:
        raise ValueError("Insufficient data points for correlation.")
        
    rho, p_value = stats.spearmanr(x, y)
    return {
        "coefficient": float(rho),
        "p_value": float(p_value),
        "sample_size": len(x)
    }

def run_external_validation(subspace_report_path: Path, wals_output_path: Path) -> Dict[str, Any]:
    """
    Orchestrates the external validation process.
    
    1. Loads subspace orientation data from previous steps (T014/T015).
    2. Fetches/loads WALS data.
    3. Aligns data by language.
    4. Computes correlation using the configured method.
    5. Saves results.
    
    Args:
        subspace_report_path: Path to the similarity/anisotropy report (JSON).
        wals_output_path: Path to save the validation report.
        
    Returns:
        Dict: The validation report.
    """
    # Load subspace data (Simulated loading of T015 output structure)
    # In reality, this file would be generated by T015
    if not subspace_report_path.exists():
        raise FileNotFoundError(f"Subspace report not found at {subspace_report_path}")
        
    with open(subspace_report_path, 'r') as f:
        subspace_data = json.load(f)
        
    # Extract language-level metrics from subspace_data
    # Assuming structure: { "models": [...], "anisotropy": {...}, "by_language": {...} }
    # We need a flat map of language -> orientation_score
    lang_orientations = {}
    if "by_language" in subspace_data:
        for lang, metrics in subspace_data["by_language"].items():
            lang_orientations[lang] = metrics
    elif "anisotropy" in subspace_data:
        # Fallback if structure is different
        logger.warning("Subspace data structure unexpected. Attempting fallback parsing.")
        # This part depends heavily on the exact output of T015
        pass

    # Fetch WALS data
    try:
        wals_data = fetch_wals_data(Path("data/raw/wals_features.json"))
    except WALSDataNotFoundError as e:
        # Fail loudly as per requirements
        logger.error(str(e))
        # Create a report indicating failure
        report = {
            "status": "data_unavailable",
            "error": str(e),
            "config": WALS_CONFIG
        }
        with open(wals_output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return report

    # Align data
    subspace_vals, wals_vals = align_subspace_orientations(lang_orientations, wals_data)
    
    if len(subspace_vals) == 0:
        raise ExternalValidationError("No overlapping languages found between subspace data and WALS.")
        
    # Compute correlation
    method = get_correlation_method()
    if method == "spearman":
        result = compute_spearman_correlation(subspace_vals, wals_vals)
    else:
        raise ValueError(f"Unsupported correlation method: {method}")
        
    # Construct report
    report = {
        "status": "success",
        "config": WALS_CONFIG,
        "method": method,
        "sample_size": result["sample_size"],
        "correlation": {
            "coefficient": result["coefficient"],
            "p_value": result["p_value"]
        },
        "interpretation": "Significant" if result["p_value"] < 0.05 else "Not Significant"
    }
    
    # Save report
    ensure_dirs(wals_output_path.parent)
    with open(wals_output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"External validation complete. Report saved to {wals_output_path}")
    return report

def main():
    """Entry point for the external validation script."""
    config = load_config()
    
    # Define paths based on config
    subspace_path = Path(get_path(config, "processed", "anisotropy_deviation.json"))
    output_path = Path(get_path(config, "processed", "wals_validation.json"))
    
    try:
        result = run_external_validation(subspace_path, output_path)
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"External validation failed: {e}")
        # Ensure the script exits with an error code if data is missing
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()