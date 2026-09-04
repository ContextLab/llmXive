"""
Group-level analysis for RSA metrics.
Implements Fisher's Z transformation and aggregation across subjects.
"""
import numpy as np
import json
import logging
from pathlib import Path
import code.config as config
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fisher_z_transform(r: float) -> float:
    """
    Apply Fisher's Z transformation to a correlation coefficient.
    
    Formula: Z = 0.5 * ln((1+r)/(1-r))
    
    Args:
        r: Correlation coefficient (-1 < r < 1)
        
    Returns:
        Fisher's Z transformed value
        
    Raises:
        ValueError: If r is outside the valid range (-1, 1)
    """
    if not -1 < r < 1:
        raise ValueError(f"Correlation coefficient must be in (-1, 1), got {r}")
    
    return 0.5 * np.log((1 + r) / (1 - r))


def inverse_fisher_z(z: float) -> float:
    """
    Inverse Fisher's Z transformation to recover correlation coefficient.
    
    Formula: r = (exp(2Z) - 1) / (exp(2Z) + 1)
    
    Args:
        z: Fisher's Z transformed value
        
    Returns:
        Correlation coefficient
    """
    return (np.exp(2 * z) - 1) / (np.exp(2 * z) + 1)


def aggregate_group_stats(
    subject_results: List[Dict[str, Any]], 
    metric_key: str = "early_late"
) -> Dict[str, float]:
    """
    Aggregate RSA metrics across subjects using Fisher's Z transformation.
    
    Steps:
    1. Transform each subject's correlation to Z-score
    2. Compute mean Z-score across subjects
    3. Transform back to correlation coefficient
    4. Compute standard deviation and standard error
    
    Args:
        subject_results: List of dictionaries, each containing ROI metrics
        metric_key: Key in the dictionary to aggregate (e.g., "early_late", "early_early")
        
    Returns:
        Dictionary with aggregated statistics per ROI
    """
    if not subject_results:
        raise ValueError("No subject results provided for aggregation")
    
    # Collect all ROIs from the first subject
    rois = list(subject_results[0].keys())
    
    aggregated_stats = {}
    
    for roi in rois:
        z_scores = []
        
        for subject_data in subject_results:
            if roi not in subject_data:
                logger.warning(f"ROI {roi} missing in subject data, skipping")
                continue
            
            r_val = subject_data[roi].get(metric_key)
            if r_val is None:
                logger.warning(f"Metric {metric_key} missing for ROI {roi} in subject data, skipping")
                continue
            
            try:
                z = fisher_z_transform(r_val)
                z_scores.append(z)
            except ValueError as e:
                logger.error(f"Invalid correlation value {r_val} for ROI {roi}: {e}")
                continue
        
        if not z_scores:
            logger.warning(f"No valid Z-scores for ROI {roi}, skipping aggregation")
            continue
        
        mean_z = np.mean(z_scores)
        std_z = np.std(z_scores, ddof=1) if len(z_scores) > 1 else 0.0
        sem_z = std_z / np.sqrt(len(z_scores))
        
        # Transform back to correlation
        mean_r = inverse_fisher_z(mean_z)
        
        aggregated_stats[roi] = {
            "mean_r": float(mean_r),
            "mean_z": float(mean_z),
            "std_z": float(std_z),
            "sem_z": float(sem_z),
            "n_subjects": len(z_scores)
        }
    
    return aggregated_stats


def run_group_rsa_analysis(
    input_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Main function to run group-level RSA analysis.
    
    Loads individual subject RSA results, aggregates them using Fisher's Z,
    and saves the group statistics.
    
    Args:
        input_path: Path to the directory containing subject RSA JSON files
        output_path: Path to save the aggregated group statistics JSON
        
    Returns:
        Dictionary containing the aggregated statistics
    """
    logger.info(f"Loading subject RSA results from {input_path}")
    
    subject_results = []
    input_path = Path(input_path)
    
    # Load all JSON files from the input directory
    json_files = sorted(input_path.glob("rsa_subject_*.json"))
    
    if not json_files:
        raise FileNotFoundError(f"No RSA result files found in {input_path}")
    
    for json_file in json_files:
        logger.info(f"Loading {json_file.name}")
        with open(json_file, 'r') as f:
            subject_data = json.load(f)
            subject_results.append(subject_data)
    
    logger.info(f"Loaded {len(subject_results)} subject results")
    
    # Aggregate statistics for early_late and early_early metrics
    early_late_stats = aggregate_group_stats(subject_results, metric_key="early_late")
    early_early_stats = aggregate_group_stats(subject_results, metric_key="early_early")
    
    # Combine results
    group_stats = {
        "early_late": early_late_stats,
        "early_early": early_early_stats,
        "n_subjects": len(subject_results),
        "method": "Fisher's Z transformation"
    }
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(group_stats, f, indent=2)
    
    logger.info(f"Group RSA statistics saved to {output_path}")
    
    return group_stats


def main():
    """
    Entry point for the group RSA analysis script.
    """
    # Define paths using config
    input_dir = config.get_data_path("processed/rsa_results")
    output_file = config.get_output_path("group_rsa_stats.json")
    
    logger.info("Starting group RSA analysis")
    
    try:
        results = run_group_rsa_analysis(input_dir, output_file)
        logger.info("Group RSA analysis completed successfully")
        
        # Print summary
        logger.info(f"Analyzed {results['n_subjects']} subjects")
        for roi, stats in results['early_late'].items():
            logger.info(f"ROI {roi}: mean_r = {stats['mean_r']:.4f} (n={stats['n_subjects']})")
            
    except Exception as e:
        logger.error(f"Group RSA analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()