"""
Group-level statistical analysis for RSA results.
Implements Fisher's Z transformation and aggregation across subjects.
"""
import numpy as np
import json
import logging
from pathlib import Path
import code.config as config

logger = logging.getLogger(__name__)

def fisher_z_transform(r):
    """
    Apply Fisher's Z transformation to a correlation coefficient.
    Z = 0.5 * ln((1+r)/(1-r))

    Parameters
    ----------
    r : float or np.ndarray
        Correlation coefficient(s) in range [-1, 1].

    Returns
    -------
    float or np.ndarray
        Fisher's Z transformed value(s).
    """
    # Clamp r to avoid division by zero or log of negative numbers
    # due to numerical precision issues at boundaries
    r_clamped = np.clip(r, -0.999999, 0.999999)
    return 0.5 * np.log((1 + r_clamped) / (1 - r_clamped))

def inverse_fisher_z(z):
    """
    Apply inverse Fisher's Z transformation.
    r = (exp(2z) - 1) / (exp(2z) + 1)

    Parameters
    ----------
    z : float or np.ndarray
        Fisher's Z value(s).

    Returns
    -------
    float or np.ndarray
        Correlation coefficient(s).
    """
    return (np.exp(2 * z) - 1) / (np.exp(2 * z) + 1)

def aggregate_group_stats(roi_stats_list):
    """
    Aggregate Fisher's Z transformed statistics across subjects.

    Parameters
    ----------
    roi_stats_list : list of dict
        List of dictionaries, one per subject, containing RSA statistics.
        Each dict should have structure:
        {
            "roi_name": {
                "early_late": float,  # correlation or dissimilarity
                "early_early": float
            },
            ...
        }

    Returns
    -------
    dict
        Aggregated group statistics with mean, std, and N subjects.
        Structure:
        {
            "roi_name": {
                "early_late": {
                    "mean_r": float,
                    "mean_z": float,
                    "std_z": float,
                    "n_subjects": int
                },
                "early_early": {
                    "mean_r": float,
                    "mean_z": float,
                    "std_z": float,
                    "n_subjects": int
                }
            }
        }
    """
    if not roi_stats_list:
        raise ValueError("roi_stats_list cannot be empty")

    # Collect all ROI names from the first subject
    all_rois = set(roi_stats_list[0].keys())

    # Verify all subjects have the same ROIs
    for i, stats in enumerate(roi_stats_list[1:], 1):
        if set(stats.keys()) != all_rois:
            logger.warning(f"Subject {i} has different ROIs. Using intersection.")
            all_rois = all_rois.intersection(set(stats.keys()))

    if not all_rois:
        raise ValueError("No common ROIs found across subjects")

    aggregated = {}

    for roi in all_rois:
        aggregated[roi] = {}

        for metric in ["early_late", "early_early"]:
            # Collect values for this metric across subjects
            values = []
            for subject_stats in roi_stats_list:
                if roi in subject_stats and metric in subject_stats[roi]:
                    r_val = subject_stats[roi][metric]
                    values.append(r_val)

            if not values:
                logger.warning(f"No data for {roi}/{metric} across subjects")
                continue

            values = np.array(values)

            # Transform to Fisher's Z
            z_values = fisher_z_transform(values)

            # Compute mean and std in Z-space
            mean_z = np.mean(z_values)
            std_z = np.std(z_values, ddof=1) if len(z_values) > 1 else 0.0

            # Transform mean back to correlation space
            mean_r = inverse_fisher_z(mean_z)

            aggregated[roi][metric] = {
                "mean_r": float(mean_r),
                "mean_z": float(mean_z),
                "std_z": float(std_z),
                "n_subjects": len(values)
            }

    return aggregated

def run_group_rsa_analysis(input_dir=None, output_path=None):
    """
    Main function to run group-level RSA analysis.
    Loads individual subject RSA results, applies Fisher's Z transformation,
    and aggregates statistics.

    Parameters
    ----------
    input_dir : str or Path, optional
        Directory containing individual subject RSA JSON files.
        Defaults to config.get_data_path() / 'results'.
    output_path : str or Path, optional
        Path for the output JSON file.
        Defaults to config.get_output_path() / 'group_rsa_stats.json'.

    Returns
    -------
    dict
        The aggregated group statistics dictionary.
    """
    if input_dir is None:
        input_dir = config.get_data_path() / 'results'
    else:
        input_dir = Path(input_dir)

    if output_path is None:
        output_path = config.get_output_path() / 'group_rsa_stats.json'
    else:
        output_path = Path(output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Find all subject RSA files
    input_dir = Path(input_dir)
    rsa_files = sorted(input_dir.glob('rsa_*.json'))

    if not rsa_files:
        # Try looking for files with pattern matching individual subjects
        # e.g., results/sub-01_rsa.json, results/sub-02_rsa.json, etc.
        rsa_files = sorted(input_dir.glob('sub-*_rsa.json'))

    if not rsa_files:
        # Try looking for results/rsa_matrices.json if only one file exists
        single_file = input_dir / 'rsa_matrices.json'
        if single_file.exists():
            # This might be a combined file, try to load and process
            logger.info(f"Found single RSA file: {single_file}")
            with open(single_file, 'r') as f:
                # Assume it's a dict where keys are subject IDs
                data = json.load(f)
                if isinstance(data, dict):
                    # Filter out non-subject keys if any
                    subject_data = {k: v for k, v in data.items() 
                                   if k.startswith('sub-') or k.startswith('subject')}
                    if subject_data:
                        roi_stats_list = list(subject_data.values())
                    else:
                        roi_stats_list = [data]
                else:
                    roi_stats_list = [data]
            logger.info(f"Processed {len(roi_stats_list)} subjects from single file")
        else:
            raise FileNotFoundError(
                f"No RSA result files found in {input_dir}. "
                f"Expected pattern: rsa_*.json or sub-*_rsa.json"
            )
    else:
        # Load each subject's RSA results
        roi_stats_list = []
        for rsa_file in rsa_files:
            logger.info(f"Loading RSA results from {rsa_file}")
            with open(rsa_file, 'r') as f:
                subject_data = json.load(f)
            
            # Handle both single-subject and multi-subject formats
            if isinstance(subject_data, dict):
                # If it has ROI keys directly, assume it's a single subject result
                if any(k in ['early_late', 'early_early'] for v in subject_data.values() 
                       if isinstance(v, dict) for k in v.keys()):
                    roi_stats_list.append(subject_data)
                else:
                    # Might be a combined file, try to extract subject data
                    # This is a fallback for unexpected formats
                    logger.warning(f"Unexpected format in {rsa_file}, treating as single subject")
                    roi_stats_list.append(subject_data)
            elif isinstance(subject_data, list):
                roi_stats_list.extend(subject_data)
            else:
                logger.warning(f"Unexpected data type in {rsa_file}: {type(subject_data)}")

    if not roi_stats_list:
        raise ValueError("No valid RSA data loaded from input files")

    logger.info(f"Aggregating data from {len(roi_stats_list)} subjects")

    # Perform aggregation
    aggregated_stats = aggregate_group_stats(roi_stats_list)

    # Add metadata
    result = {
        "n_subjects": len(roi_stats_list),
        "analysis_type": "Fisher's Z aggregation",
        "formula": "Z = 0.5 * ln((1+r)/(1-r))",
        "results": aggregated_stats
    }

    # Write output
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Group RSA statistics written to {output_path}")

    return result

def main():
    """Entry point for command-line execution."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    result = run_group_rsa_analysis()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
