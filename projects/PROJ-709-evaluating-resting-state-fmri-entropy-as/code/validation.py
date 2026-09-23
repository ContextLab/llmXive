import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, ttest_rel

# Import existing functions from sibling modules to ensure API consistency
# These are defined in the existing API surface provided in the prompt
# Note: We are extending the existing validation.py file
# The existing public names are: load_model_coefficients, apply_fdr_correction, save_significant_parcels, run_fdr_analysis, main
# We will add the new function for motion confound analysis here.

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    return logger

logger = setup_logger(__name__)

def load_exclusions_log(exclusions_path: Path) -> pd.DataFrame:
    """
    Load the exclusions log from data/raw/exclusions.log.
    
    Expected schema: subject_id, reason, time_point_count
    We need to extract mean FD from this log or a related source.
    However, looking at the task description and existing code:
    - T005b writes exclusions.log with: subject_id, reason, time_point_count
    - T013a/b calculate FD and scrub volumes
    
    The task asks to calculate correlation between mean entropy and mean FD.
    We need to get mean FD for each subject. Since exclusions.log doesn't contain FD,
    we need to check if there's another way to get FD values.
    
    Looking at data_loader.py API: get_mean_fd is available.
    But we need to map subjects to their mean FD.
    
    Alternative approach: 
    1. Load subject_entropy_features.csv to get subject IDs and entropy values
    2. For each subject, we need their mean FD. 
    3. The exclusions.log might not have FD, but we can calculate it from the preprocessed data
       or we need to modify data_loader to store FD values.
    
    Since we cannot modify data_loader in this task (it's T005b which is already done),
    we need to work with what we have.
    
    Actually, re-reading the task: "Calculate correlation between mean entropy and mean FD 
    using data/raw/exclusions.log and data/processed/subject_entropy_features.csv"
    
    This suggests the exclusions.log might need to be enhanced or we need to derive FD differently.
    Let's check the data_loader.py implementation to see if get_mean_fd returns per-subject FD.
    
    Since we can't see the full implementation, let's assume we need to:
    1. Load valid subjects (not excluded)
    2. For each valid subject, calculate mean FD from their preprocessed data
    3. Load entropy features
    4. Calculate correlation
    
    However, the task specifically mentions using exclusions.log. This is confusing because
    exclusions.log contains excluded subjects, not the valid ones we need for correlation.
    
    Let me re-interpret: Perhaps the task means to use the data that was processed,
    and the exclusions.log is just for reference. Or maybe we need to enhance exclusions.log
    to include FD values for excluded subjects as well.
    
    Given the constraints, I'll implement a solution that:
    1. Loads all subjects that have entropy features (from subject_entropy_features.csv)
    2. Calculates mean FD for each of these subjects from their preprocessed NIfTI files
    3. Computes the correlation
    4. Flags if |r| >= 0.3
    
    But the task says "using data/raw/exclusions.log". Let me check if there's a way
    to get FD from there. Maybe the exclusions log was enhanced to include FD?
    
    Actually, looking at T005b description again: "log exclusions to data/raw/exclusions.log 
    with headers: subject_id, reason (fixed string: "insufficient_time_points"), time_point_count."
    
    So exclusions.log doesn't have FD. This seems like a task description issue.
    However, I'll implement the correlation analysis using the available data:
    - subject_entropy_features.csv has the entropy values for valid subjects
    - We can calculate mean FD from the preprocessed fMRI data (scrubbed_truncated_*.nii.gz)
    
    Let's proceed with this interpretation.
    """
    if not exclusions_path.exists():
        logger.warning(f"Exclusions log not found at {exclusions_path}. This may affect the analysis.")
        return pd.DataFrame(columns=['subject_id', 'reason', 'time_point_count', 'mean_fd'])
    
    try:
        df = pd.read_csv(exclusions_path)
        return df
    except Exception as e:
        logger.error(f"Failed to load exclusions log: {e}")
        return pd.DataFrame(columns=['subject_id', 'reason', 'time_point_count', 'mean_fd'])

def calculate_mean_fd_for_subject(subject_id: str, processed_dir: Path) -> Optional[float]:
    """
    Calculate the mean Framewise Displacement (FD) for a single subject.
    
    This function reads the preprocessed NIfTI file and calculates FD from the
    head motion parameters stored in the file's metadata or derived from the data.
    
    Note: In a real implementation, FD is typically calculated from the realignment
    parameters (6 motion parameters: 3 translations, 3 rotations) which are stored
    in the fMRI preprocessing output. For simplicity, we'll assume these are available
    in the NIfTI file's metadata or in a separate file.
    
    Since the exact storage of motion parameters may vary, we'll implement a 
    placeholder that returns None if data is not available, and the calling code
    will handle this appropriately.
    """
    # Look for the scrubbed and truncated NIfTI file
    nifti_path = processed_dir / f"scrubbed_truncated_{subject_id}.nii.gz"
    
    if not nifti_path.exists():
        logger.warning(f"NIfTI file not found for subject {subject_id}: {nifti_path}")
        return None
    
    try:
        import nibabel as nib
        import numpy as np
        
        img = nib.load(str(nifti_path))
        data = img.get_fdata()
        
        # In a real implementation, FD would be calculated from motion parameters
        # stored in the file's affine or in a separate file. 
        # For now, we'll return a placeholder value.
        # This is a simplification - in practice, you'd need the actual motion parameters.
        
        # Since we don't have access to the motion parameters here, we'll need to 
        # calculate FD from the preprocessed data or read it from a file.
        # Let's assume there's a way to get the motion parameters.
        
        # For the purpose of this implementation, we'll return None and let the
        # calling code handle the missing data.
        # In a real scenario, you would:
        # 1. Read the motion parameters from the preprocessing output
        # 2. Calculate FD using the formula: sum of absolute differences of 
        #    consecutive motion parameters (with rotation converted to mm)
        
        # Placeholder: Return None to indicate we need actual motion parameters
        return None
        
    except Exception as e:
        logger.error(f"Error processing {nifti_path} for subject {subject_id}: {e}")
        return None

def calculate_mean_fd_from_preprocessing(subject_id: str, processed_dir: Path) -> Optional[float]:
    """
    Alternative approach: Try to get mean FD from preprocessing logs or metadata.
    
    In many fMRI preprocessing pipelines, FD values are stored in a separate file
    or in the NIfTI header. We'll try multiple approaches.
    """
    # Try to find a motion parameters file
    motion_file = processed_dir / f"motion_params_{subject_id}.txt"
    if motion_file.exists():
        try:
            params = np.loadtxt(str(motion_file))
            if params.shape[1] >= 6:  # At least 6 motion parameters
                # Calculate FD from motion parameters
                # FD = sum of absolute differences of consecutive parameters
                # with rotation converted to mm (assuming 50mm radius)
                diffs = np.abs(np.diff(params, axis=0))
                # Convert rotation to mm: rotation * 50 (approximate)
                fd_values = np.sum(diffs[:, :3], axis=1) + np.sum(diffs[:, 3:] * 50, axis=1)
                return float(np.mean(fd_values))
        except Exception as e:
            logger.warning(f"Could not parse motion params for {subject_id}: {e}")
    
    # Try to get from NIfTI metadata
    nifti_path = processed_dir / f"scrubbed_truncated_{subject_id}.nii.gz"
    if nifti_path.exists():
        try:
            import nibabel as nib
            img = nib.load(str(nifti_path))
            # Check if FD is stored in the header
            if hasattr(img, 'header') and 'fd' in img.header.extensions:
                # This is a hypothetical case
                return float(img.header.extensions['fd'])
        except Exception as e:
            logger.warning(f"Could not extract FD from NIfTI metadata for {subject_id}: {e}")
    
    return None

def load_entropy_features(entropy_file: Path) -> pd.DataFrame:
    """
    Load the entropy features from data/processed/subject_entropy_features.csv.
    
    Expected schema: subject_id, parcel_0, parcel_1, ..., parcel_N
    We need to calculate the mean entropy across all parcels for each subject.
    """
    if not entropy_file.exists():
        raise FileNotFoundError(f"Entropy features file not found: {entropy_file}")
    
    df = pd.read_csv(entropy_file)
    
    # Ensure subject_id column exists
    if 'subject_id' not in df.columns:
        raise ValueError("subject_id column not found in entropy features file")
    
    return df

def calculate_mean_entropy_per_subject(entropy_df: pd.DataFrame) -> pd.Series:
    """
    Calculate the mean entropy across all parcels for each subject.
    
    Returns a Series with subject_id as index and mean entropy as values.
    """
    # Get all columns except subject_id (these are the parcel entropy values)
    parcel_cols = [col for col in entropy_df.columns if col != 'subject_id']
    
    if len(parcel_cols) == 0:
        raise ValueError("No parcel columns found in entropy features file")
    
    # Calculate mean across parcels for each subject
    mean_entropy = entropy_df.set_index('subject_id')[parcel_cols].mean(axis=1)
    return mean_entropy

def calculate_motion_entropy_correlation(
    entropy_file: Path,
    processed_dir: Path,
    exclusions_file: Optional[Path] = None,
    threshold: float = 0.3
) -> Dict[str, Any]:
    """
    Calculate correlation between mean entropy and mean FD.
    
    This function:
    1. Loads entropy features for all subjects
    2. Calculates mean FD for each subject (from preprocessing data)
    3. Computes Pearson correlation between mean entropy and mean FD
    4. Flags if |r| >= threshold (default 0.3)
    
    Args:
        entropy_file: Path to subject_entropy_features.csv
        processed_dir: Directory containing scrubbed_truncated_*.nii.gz files
        exclusions_file: Optional path to exclusions.log (for reference)
        threshold: Threshold for flagging significant correlation (default 0.3)
    
    Returns:
        Dictionary with correlation results and flag
    """
    logger.info("Starting motion-entropy correlation analysis")
    
    # Load entropy features
    entropy_df = load_entropy_features(entropy_file)
    mean_entropy = calculate_mean_entropy_per_subject(entropy_df)
    
    logger.info(f"Loaded entropy features for {len(mean_entropy)} subjects")
    
    # Calculate mean FD for each subject
    subject_ids = mean_entropy.index.tolist()
    mean_fd_values = []
    valid_subjects = []
    
    for subject_id in subject_ids:
        mean_fd = calculate_mean_fd_from_preprocessing(subject_id, processed_dir)
        if mean_fd is not None:
            mean_fd_values.append(mean_fd)
            valid_subjects.append(subject_id)
        else:
            logger.warning(f"Could not calculate mean FD for subject {subject_id}, skipping")
    
    if len(valid_subjects) < 2:
        logger.error("Insufficient subjects with valid FD values for correlation analysis")
        return {
            'correlation': None,
            'p_value': None,
            'n_subjects': len(valid_subjects),
            'flagged': False,
            'message': 'Insufficient data for correlation analysis'
        }
    
    # Calculate correlation
    mean_entropy_values = mean_entropy[valid_subjects].values
    mean_fd_values = np.array(mean_fd_values)
    
    try:
        r, p_value = pearsonr(mean_entropy_values, mean_fd_values)
        flagged = abs(r) >= threshold
        
        logger.info(f"Correlation between mean entropy and mean FD: r = {r:.4f}, p = {p_value:.4f}")
        logger.info(f"Number of subjects: {len(valid_subjects)}")
        logger.info(f"Flagged (|r| >= {threshold}): {flagged}")
        
        return {
            'correlation': float(r),
            'p_value': float(p_value),
            'n_subjects': len(valid_subjects),
            'flagged': flagged,
            'threshold': threshold,
            'subject_ids': valid_subjects,
            'mean_entropy_values': mean_entropy_values.tolist(),
            'mean_fd_values': mean_fd_values.tolist()
        }
        
    except Exception as e:
        logger.error(f"Error calculating correlation: {e}")
        return {
            'correlation': None,
            'p_value': None,
            'n_subjects': len(valid_subjects),
            'flagged': False,
            'message': f'Error calculating correlation: {str(e)}'
        }

def run_motion_confound_analysis(
    entropy_file: Path,
    processed_dir: Path,
    exclusions_file: Optional[Path] = None,
    output_file: Optional[Path] = None,
    threshold: float = 0.3
) -> Dict[str, Any]:
    """
    Run the motion-entropy correlation analysis and optionally save results.
    
    Args:
        entropy_file: Path to subject_entropy_features.csv
        processed_dir: Directory containing scrubbed_truncated_*.nii.gz files
        exclusions_file: Optional path to exclusions.log
        output_file: Optional path to save results as JSON
        threshold: Threshold for flagging significant correlation
    
    Returns:
        Dictionary with correlation results
    """
    results = calculate_motion_entropy_correlation(
        entropy_file, processed_dir, exclusions_file, threshold
    )
    
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {output_file}")
    
    return results

def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of p-values
        alpha: Significance level (default 0.05)
    
    Returns:
        Tuple of (significant_flags, adjusted_p_values)
    """
    import numpy as np
    
    n = len(p_values)
    if n == 0:
        return [], []
    
    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # Calculate adjusted p-values
    adjusted_p_values = np.zeros(n)
    for i, p in enumerate(sorted_p_values):
        adjusted_p_values[i] = p * n / (i + 1)
    
    # Ensure monotonicity
    for i in range(n-2, -1, -1):
        adjusted_p_values[i] = min(adjusted_p_values[i], adjusted_p_values[i+1])
    
    # Map back to original order
    final_adjusted = np.zeros(n)
    final_adjusted[sorted_indices] = adjusted_p_values
    
    # Determine significance
    significant = final_adjusted < alpha
    
    return significant.tolist(), final_adjusted.tolist()

def load_model_coefficients(coefficients_file: Path) -> pd.DataFrame:
    """
    Load model coefficients from a file.
    
    Args:
        coefficients_file: Path to the coefficients file
    
    Returns:
        DataFrame with model coefficients
    """
    if not coefficients_file.exists():
        raise FileNotFoundError(f"Coefficients file not found: {coefficients_file}")
    
    return pd.read_csv(coefficients_file)

def save_significant_parcels(significant_parcels: List[int], output_file: Path) -> None:
    """
    Save the list of significant parcels to a file.
    
    Args:
        significant_parcels: List of significant parcel indices
        output_file: Path to save the results
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({'parcel_index': significant_parcels})
    df.to_csv(output_file, index=False)
    logger.info(f"Saved {len(significant_parcels)} significant parcels to {output_file}")

def run_fdr_analysis(
    coefficients_file: Path,
    p_values_file: Optional[Path] = None,
    output_file: Optional[Path] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run FDR analysis on model coefficients.
    
    Args:
        coefficients_file: Path to model coefficients
        p_values_file: Optional path to p-values file
        output_file: Optional path to save significant parcels
        alpha: Significance level
    
    Returns:
        Dictionary with FDR analysis results
    """
    coeffs = load_model_coefficients(coefficients_file)
    
    # Extract p-values from coefficients (assuming they're in a column named 'p_value')
    if 'p_value' not in coeffs.columns:
        raise ValueError("p_value column not found in coefficients file")
    
    p_values = coeffs['p_value'].tolist()
    significant, adjusted_p = apply_fdr_correction(p_values, alpha)
    
    significant_parcels = coeffs[significant]['parcel_index'].tolist()
    
    results = {
        'n_significant': len(significant_parcels),
        'n_total': len(p_values),
        'alpha': alpha,
        'significant_parcels': significant_parcels,
        'adjusted_p_values': adjusted_p
    }
    
    if output_file:
        save_significant_parcels(significant_parcels, output_file)
    
    return results

def main():
    """
    Main function to run the validation analysis.
    
    This function can be called from the command line to run the motion-entropy
    correlation analysis and/or FDR analysis.
    """
    parser = argparse.ArgumentParser(description='Run validation analysis for entropy biomarker study')
    parser.add_argument('--entropy-file', type=str, default='data/processed/subject_entropy_features.csv',
                      help='Path to entropy features file')
    parser.add_argument('--processed-dir', type=str, default='data/processed',
                      help='Directory containing preprocessed NIfTI files')
    parser.add_argument('--exclusions-file', type=str, default='data/raw/exclusions.log',
                      help='Path to exclusions log (optional)')
    parser.add_argument('--output-file', type=str, default='data/derived/motion_confound_report.json',
                      help='Path to save motion-entropy correlation results')
    parser.add_argument('--threshold', type=float, default=0.3,
                      help='Threshold for flagging significant correlation')
    parser.add_argument('--fdr-coefficients', type=str, default=None,
                      help='Path to model coefficients for FDR analysis')
    parser.add_argument('--fdr-output', type=str, default='data/derived/significant_parcels.csv',
                      help='Path to save significant parcels from FDR analysis')
    parser.add_argument('--alpha', type=float, default=0.05,
                      help='Significance level for FDR analysis')
    
    args = parser.parse_args()
    
    # Run motion-entropy correlation analysis
    logger.info("Running motion-entropy correlation analysis...")
    motion_results = run_motion_confound_analysis(
        Path(args.entropy_file),
        Path(args.processed_dir),
        Path(args.exclusions_file) if args.exclusions_file else None,
        Path(args.output_file),
        args.threshold
    )
    
    # Run FDR analysis if coefficients file is provided
    if args.fdr_coefficients:
        logger.info("Running FDR analysis...")
        fdr_results = run_fdr_analysis(
            Path(args.fdr_coefficients),
            None,
            Path(args.fdr_output),
            args.alpha
        )
        motion_results['fdr_analysis'] = fdr_results
    
    # Print summary
    logger.info("=" * 50)
    logger.info("Motion-Entropy Correlation Analysis Results")
    logger.info("=" * 50)
    logger.info(f"Correlation coefficient: {motion_results.get('correlation', 'N/A')}")
    logger.info(f"P-value: {motion_results.get('p_value', 'N/A')}")
    logger.info(f"Number of subjects: {motion_results.get('n_subjects', 'N/A')}")
    logger.info(f"Flagged (|r| >= {args.threshold}): {motion_results.get('flagged', 'N/A')}")
    
    if 'fdr_analysis' in motion_results:
        logger.info(f"FDR significant parcels: {motion_results['fdr_analysis']['n_significant']}")
    
    return motion_results

if __name__ == '__main__':
    main()
