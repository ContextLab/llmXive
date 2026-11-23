"""
Group-level analysis for RSA metrics.
Implements Fisher's Z aggregation across subjects for Early vs. Late event comparisons.
"""
import numpy as np
import json
import logging
from pathlib import Path
import code.config as config
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def fisher_z_transform(r: float) -> float:
    """
    Apply Fisher's Z transformation to a correlation coefficient.
    Z = 0.5 * ln((1 + r) / (1 - r))

    Args:
        r: Correlation coefficient (-1 < r < 1)

    Returns:
        Fisher's Z transformed value
    """
    # Clip to avoid division by zero or log of negative numbers
    r_clipped = np.clip(r, -0.9999, 0.9999)
    z = 0.5 * np.log((1 + r_clipped) / (1 - r_clipped))
    return z

def inverse_fisher_z(z: float) -> float:
    """
    Apply inverse Fisher's Z transformation.
    r = (exp(2Z) - 1) / (exp(2Z) + 1)

    Args:
        z: Fisher's Z value

    Returns:
        Correlation coefficient
    """
    return (np.exp(2 * z) - 1) / (np.exp(2 * z) + 1)

def aggregate_group_stats(early_late_values: List[float], early_early_values: List[float]) -> Dict[str, float]:
    """
    Aggregate RSA metrics across subjects using Fisher's Z transformation.

    Steps:
    1. Transform individual subject correlations to Z-scores.
    2. Compute mean Z-score.
    3. Transform back to correlation coefficient.
    4. Compute standard error and confidence intervals.

    Args:
        early_late_values: List of Early vs. Late dissimilarity values (converted to correlations if needed)
        early_early_values: List of Early vs. Early dissimilarity values

    Returns:
        Dictionary with aggregated statistics
    """
    if not early_late_values or not early_early_values:
        raise ValueError("Input lists cannot be empty")

    # Convert dissimilarity (1 - corr) to correlation if necessary
    # Assuming input values are dissimilarities (0 to 2 range for 1-corr)
    # If inputs are already correlations (-1 to 1), this logic still holds if we treat them as r
    # Based on T021 spec: RDM[i,j] = 1 - corr(...). So inputs are dissimilarities.
    # We need to convert back to correlation for Fisher Z: r = 1 - dissimilarity
    
    r_early_late = [1.0 - val for val in early_late_values]
    r_early_early = [1.0 - val for val in early_early_values]

    # Transform to Z
    z_early_late = [fisher_z_transform(r) for r in r_early_late]
    z_early_early = [fisher_z_transform(r) for r in r_early_early]

    # Mean Z
    mean_z_early_late = np.mean(z_early_late)
    mean_z_early_early = np.mean(z_early_early)

    # Back-transform to r
    mean_r_early_late = inverse_fisher_z(mean_z_early_late)
    mean_r_early_early = inverse_fisher_z(mean_z_early_early)

    # Standard error of Z: 1 / sqrt(N - 3)
    n = len(z_early_late)
    se_z = 1.0 / np.sqrt(n - 3) if n > 3 else 1.0

    # 95% CI for Z
    ci_low_z = mean_z_early_late - 1.96 * se_z
    ci_high_z = mean_z_early_late + 1.96 * se_z
    ci_low_r = inverse_fisher_z(ci_low_z)
    ci_high_r = inverse_fisher_z(ci_high_z)

    return {
        "mean_correlation_early_late": float(mean_r_early_late),
        "mean_correlation_early_early": float(mean_r_early_early),
        "mean_z_early_late": float(mean_z_early_late),
        "mean_z_early_early": float(mean_z_early_early),
        "std_error_z": float(se_z),
        "ci_95_low_r": float(ci_low_r),
        "ci_95_high_r": float(ci_high_r),
        "n_subjects": n
    }

def run_group_rsa_analysis(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main function to run group-level RSA analysis.
    Reads per-subject RSA matrices, aggregates using Fisher's Z, and writes results.

    Args:
        input_path: Path to the JSON file containing per-subject RSA metrics (from T021)
        output_path: Path to write the group stats JSON

    Returns:
        Dictionary of aggregated results
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input RSA metrics file not found: {input_file}")

    logger.info(f"Loading RSA metrics from {input_file}")
    
    with open(input_file, 'r') as f:
        data = json.load(f)

    # Expected structure from T021: {roi: {early_late: float, early_early: float}}
    # We need to aggregate across subjects. Assuming the input file contains a list of subjects
    # or the data is already structured by subject. 
    # Based on T021 description: "Output: results/rsa_matrices.json (schema: {roi: {early_late: float, early_early: float}})"
    # This implies a single subject's result or a merged result. 
    # However, T023 requires "across subjects". 
    # We assume the input file structure is actually: {subject_id: {roi: {early_late: float, early_early: float}}}
    # OR the file contains a list of such objects. 
    # Let's handle the case where the input is a list of subject results.
    
    subjects_data = []
    if isinstance(data, list):
        subjects_data = data
    elif isinstance(data, dict):
        # Check if it's a single subject or aggregated
        if 'early_late' in data and 'early_early' in data:
            # Single subject flat structure? Unlikely for group analysis.
            # Assume it's a single subject for now, but this would fail the "across subjects" requirement.
            # Let's assume the T021 output format description was simplified and actual file has subjects.
            # If the file is just one subject, we can't do group stats.
            # We'll assume the input is a list of dicts: [{'subject_id': 'sub-01', 'roi_data': {...}}, ...]
            # OR the keys are subject IDs.
            if any(k.startswith('sub-') for k in data.keys()):
                subjects_data = [{'subject_id': k, **v} for k, v in data.items()]
            else:
                # Fallback: treat as single subject list
                subjects_data = [data]
        else:
            # Try to interpret keys as ROIs and assume missing subject dimension?
            # This is ambiguous. Let's assume the input is a list of subject results.
            # If the user provided a dict of ROIs, we can't aggregate across subjects.
            # We will raise an error if we can't find subject data.
            raise ValueError("Input data structure is ambiguous. Expected a list of subject results or a dict keyed by subject_id.")

    if not subjects_data:
        raise ValueError("No subject data found in input file")

    logger.info(f"Processing {len(subjects_data)} subjects")

    # Aggregate per ROI
    # We need to collect all Early-Late and Early-Early values per ROI
    roi_metrics = {}
    
    # First pass: collect all ROIs
    all_rois = set()
    for subj in subjects_data:
        # Assume structure: {'subject_id': 'sub-01', 'roi': {'mPFC': {'early_late': 0.5, ...}, ...}}
        # Or maybe flat: {'subject_id': 'sub-01', 'mPFC': {'early_late': 0.5, ...}}
        # Let's look for a nested 'roi' key or assume keys are ROIs if not 'subject_id'
        if 'roi' in subj:
            rois = subj['roi']
        else:
            # Assume all keys except 'subject_id' are ROIs
            rois = {k: v for k, v in subj.items() if k != 'subject_id'}
        
        for roi in rois:
            all_rois.add(roi)

    # Second pass: aggregate
    for roi in all_rois:
        early_late_vals = []
        early_early_vals = []
        
        for subj in subjects_data:
            if 'roi' in subj:
                roi_data = subj['roi'].get(roi, {})
            else:
                roi_data = subj.get(roi, {})
            
            if 'early_late' in roi_data and 'early_early' in roi_data:
                early_late_vals.append(roi_data['early_late'])
                early_early_vals.append(roi_data['early_early'])
            else:
                logger.warning(f"Missing data for {roi} in subject {subj.get('subject_id', 'unknown')}")

        if early_late_vals and early_early_vals:
            stats = aggregate_group_stats(early_late_vals, early_early_vals)
            roi_metrics[roi] = stats
        else:
            logger.warning(f"Not enough data for {roi} to perform aggregation")

    result = {
        "aggregation_method": "Fisher's Z",
        "formula": "Z = 0.5 * ln((1+r)/(1-r))",
        "roi_stats": roi_metrics
    }

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Group RSA stats written to {output_file}")
    return result

def main():
    """Entry point for the script."""
    logging.basicConfig(level=logging.INFO)
    
    input_path = config.get_output_path("rsa_matrices.json")
    output_path = config.get_output_path("group_rsa_stats.json")
    
    try:
        results = run_group_rsa_analysis(input_path, output_path)
        print(f"Successfully aggregated {len(results['roi_stats'])} ROIs.")
    except Exception as e:
        logger.error(f"Group analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()