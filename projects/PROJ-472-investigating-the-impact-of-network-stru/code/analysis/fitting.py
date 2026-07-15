import os
import numpy as np
import pandas as pd
import powerlaw
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
import json
import traceback

from config import get_data_root
from utils.logger import get_logger, AnalysisError, ResearchError

# Configure logger
logger = get_logger(__name__)

def load_avalanche_sizes_from_store(subject_id: str) -> List[float]:
    """
    Load avalanche sizes for a specific subject from the processed data store.
    
    Args:
        subject_id: Unique identifier for the subject
        
    Returns:
        List of avalanche sizes (floats)
        
    Raises:
        AnalysisError: If data file is missing or malformed
    """
    data_root = get_data_root()
    # Assuming avalanche data is stored in data/processed/avalanches/
    file_path = Path(data_root) / "processed" / "avalanches" / f"{subject_id}_avalanche_sizes.csv"
    
    if not file_path.exists():
        raise AnalysisError(f"Avalanche size data not found for subject {subject_id} at {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        if 'size' not in df.columns:
            raise AnalysisError(f"Column 'size' not found in {file_path}")
        
        sizes = df['size'].dropna().tolist()
        
        if not sizes:
            raise AnalysisError(f"No valid avalanche sizes found for subject {subject_id}")
        
        return sizes
    except Exception as e:
        raise AnalysisError(f"Failed to load avalanche sizes for {subject_id}: {str(e)}") from e

def fit_power_law_model(sizes: List[float], subject_id: str) -> Dict[str, Any]:
    """
    Fit a power-law model to the avalanche size distribution.
    
    This function explicitly handles convergence failures by logging a specific
    error code and raising an AnalysisError, rather than silently returning NaN.
    
    Args:
        sizes: List of avalanche sizes
        subject_id: Subject identifier for logging
        
    Returns:
        Dictionary containing fit results:
            - 'alpha': Power-law exponent
            - 'xmin': Lower bound for power-law behavior
            - 'D': KS statistic
            - 'p_value': P-value of the fit
            - 'success': Boolean indicating fit success
            - 'error_code': Error code if failed (None if success)
            - 'error_message': Error message if failed (None if success)
            
    Raises:
        AnalysisError: If the power-law fit fails to converge or is invalid
    """
    if not sizes or len(sizes) < 5:
        error_msg = f"Insufficient data points ({len(sizes)}) for power-law fitting for subject {subject_id}"
        logger.error(f"[CONVERGENCE_FAILURE] {error_msg}")
        raise AnalysisError(
            error_code="CONVERGENCE_FAILURE_INSUFFICIENT_DATA",
            message=error_msg,
            subject_id=subject_id
        )
    
    try:
        # Convert to numpy array
        data = np.array(sizes)
        
        # Filter out non-positive values (power-law requires x > 0)
        valid_mask = data > 0
        if not np.any(valid_mask):
            error_msg = f"No positive values in avalanche sizes for subject {subject_id}"
            logger.error(f"[CONVERGENCE_FAILURE] {error_msg}")
            raise AnalysisError(
                error_code="CONVERGENCE_FAILURE_NO_POSITIVE_VALUES",
                message=error_msg,
                subject_id=subject_id
            )
        
        data = data[valid_mask]
        
        if len(data) < 5:
            error_msg = f"Insufficient positive data points ({len(data)}) for power-law fitting for subject {subject_id}"
            logger.error(f"[CONVERGENCE_FAILURE] {error_msg}")
            raise AnalysisError(
                error_code="CONVERGENCE_FAILURE_INSUFFICIENT_DATA",
                message=error_msg,
                subject_id=subject_id
            )
        
        # Fit power-law model
        logger.info(f"Fitting power-law model for subject {subject_id} with {len(data)} data points")
        
        # Use powerlaw package with explicit parameters
        fit = powerlaw.Fit(data, discrete=True, verbose=False)
        
        # Extract parameters
        alpha = fit.alpha
        xmin = fit.xmin
        D = fit.D
        p_value = fit.power_law.p
        
        # Validate convergence
        if alpha is None or np.isnan(alpha) or np.isinf(alpha):
            error_msg = f"Power-law fit returned invalid alpha ({alpha}) for subject {subject_id}"
            logger.error(f"[CONVERGENCE_FAILURE] {error_msg}")
            raise AnalysisError(
                error_code="CONVERGENCE_FAILURE_INVALID_ALPHA",
                message=error_msg,
                subject_id=subject_id
            )
        
        if xmin is None or np.isnan(xmin) or np.isinf(xmin):
            error_msg = f"Power-law fit returned invalid xmin ({xmin}) for subject {subject_id}"
            logger.error(f"[CONVERGENCE_FAILURE] {error_msg}")
            raise AnalysisError(
                error_code="CONVERGENCE_FAILURE_INVALID_XMIN",
                message=error_msg,
                subject_id=subject_id
            )
        
        # Check if the fit is statistically plausible (p-value > 0.1 is often used as a threshold)
        if p_value is not None and p_value < 0.1:
            logger.warning(f"Low p-value ({p_value:.4f}) for power-law fit of subject {subject_id}. "
                         "The power-law hypothesis may not be a good fit, but we still record the parameters.")
        
        # Perform model comparison (power-law vs exponential)
        try:
            R, p = fit.distribution_compare('power_law', 'exponential', normalized_ratio=True)
            logger.info(f"Model comparison (power-law vs exponential) for {subject_id}: R={R:.4f}, p={p:.4f}")
        except Exception as comp_err:
            logger.warning(f"Model comparison failed for {subject_id}: {str(comp_err)}")
            R, p = None, None
        
        result = {
            'alpha': float(alpha),
            'xmin': float(xmin),
            'D': float(D),
            'p_value': float(p_value) if p_value is not None else None,
            'R_vs_exponential': float(R) if R is not None else None,
            'p_vs_exponential': float(p) if p is not None else None,
            'success': True,
            'error_code': None,
            'error_message': None,
            'n_points': len(data),
            'subject_id': subject_id
        }
        
        logger.info(f"[CONVERGENCE_SUCCESS] Power-law fit successful for subject {subject_id}: "
                   f"alpha={alpha:.4f}, xmin={xmin:.2f}, p_value={p_value:.4f}")
        
        return result
        
    except powerlaw.Power_Law_FitError as e:
        error_msg = f"Power-law fit error for subject {subject_id}: {str(e)}"
        logger.error(f"[CONVERGENCE_FAILURE] {error_msg}")
        raise AnalysisError(
            error_code="CONVERGENCE_FAILURE_POWERLAW_ERROR",
            message=error_msg,
            subject_id=subject_id,
            original_exception=e
        ) from e
    except Exception as e:
        error_msg = f"Unexpected error during power-law fit for subject {subject_id}: {str(e)}"
        logger.error(f"[CONVERGENCE_FAILURE] {error_msg}")
        logger.error(traceback.format_exc())
        raise AnalysisError(
            error_code="CONVERGENCE_FAILURE_UNEXPECTED",
            message=error_msg,
            subject_id=subject_id,
            original_exception=e
        ) from e

def run_fitting_for_subject(subject_id: str) -> Dict[str, Any]:
    """
    Run the full power-law fitting pipeline for a single subject.
    
    Args:
        subject_id: Unique identifier for the subject
        
    Returns:
        Dictionary containing fit results or error information
    """
    logger.info(f"Starting power-law fitting for subject {subject_id}")
    
    try:
        # Load avalanche sizes
        sizes = load_avalanche_sizes_from_store(subject_id)
        
        # Fit power-law model
        result = fit_power_law_model(sizes, subject_id)
        
        return result
        
    except AnalysisError as e:
        # Re-raise AnalysisError to be caught by the pipeline
        raise e
    except Exception as e:
        error_msg = f"Unexpected error in run_fitting_for_subject for {subject_id}: {str(e)}"
        logger.error(error_msg)
        raise AnalysisError(
            error_code="FITTING_PIPELINE_ERROR",
            message=error_msg,
            subject_id=subject_id,
            original_exception=e
        ) from e

def generate_fitting_report(results: List[Dict[str, Any]], output_path: Path) -> Path:
    """
    Generate a detailed fitting report for all subjects.
    
    Args:
        results: List of fitting results dictionaries
        output_path: Path to save the report
        
    Returns:
        Path to the generated report file
    """
    # Separate successful and failed fits
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    # Create a DataFrame for successful fits
    if successful:
        df = pd.DataFrame(successful)
        df = df[['subject_id', 'alpha', 'xmin', 'D', 'p_value', 
                'R_vs_exponential', 'p_vs_exponential', 'n_points']]
        report_path = output_path / "power_law_fitting_results.csv"
        df.to_csv(report_path, index=False)
        logger.info(f"Saved fitting results for {len(successful)} subjects to {report_path}")
    else:
        report_path = output_path / "power_law_fitting_results.csv"
        # Create empty file with headers
        pd.DataFrame(columns=['subject_id', 'alpha', 'xmin', 'D', 'p_value', 
                            'R_vs_exponential', 'p_vs_exponential', 'n_points']).to_csv(report_path, index=False)
        logger.warning("No successful fitting results to save")
    
    # Create a summary report
    summary_path = output_path / "power_law_fitting_summary.md"
    with open(summary_path, 'w') as f:
        f.write("# Power-Law Fitting Report\n\n")
        f.write(f"Total subjects processed: {len(results)}\n")
        f.write(f"Successful fits: {len(successful)}\n")
        f.write(f"Failed fits: {len(failed)}\n\n")
        
        if failed:
            f.write("## Failed Fits\n\n")
            f.write("| Subject ID | Error Code | Error Message |\n")
            f.write("|------------|------------|---------------|\n")
            for r in failed:
                f.write(f"| {r.get('subject_id', 'Unknown')} | {r.get('error_code', 'Unknown')} | {r.get('error_message', 'Unknown')} |\n")
            f.write("\n")
        
        if successful:
            f.write("## Successful Fits\n\n")
            f.write("| Subject ID | Alpha | Xmin | P-value | N Points |\n")
            f.write("|------------|-------|------|---------|----------|\n")
            for r in successful:
                f.write(f"| {r['subject_id']} | {r['alpha']:.4f} | {r['xmin']:.2f} | {r['p_value']:.4f if r['p_value'] is not None else 'N/A'} | {r['n_points']} |\n")
    
    logger.info(f"Saved fitting summary to {summary_path}")
    return summary_path

def run_fitting_pipeline(subject_ids: List[str], output_dir: Optional[Path] = None) -> Tuple[List[Dict[str, Any]], Path]:
    """
    Run the power-law fitting pipeline for all subjects.
    
    Args:
        subject_ids: List of subject identifiers to process
        output_dir: Directory to save results (defaults to data/results)
        
    Returns:
        Tuple of (list of results, path to summary report)
    """
    if output_dir is None:
        data_root = get_data_root()
        output_dir = Path(data_root) / "results" / "fitting"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting power-law fitting pipeline for {len(subject_ids)} subjects")
    
    results = []
    failed_count = 0
    success_count = 0
    
    for subject_id in subject_ids:
        try:
            result = run_fitting_for_subject(subject_id)
            results.append(result)
            success_count += 1
        except AnalysisError as e:
            # Log the error but continue with other subjects
            # The error is recorded in the result for later exclusion from correlation
            logger.error(f"Power-law fitting failed for {subject_id}: {e.message} (Code: {e.error_code})")
            
            # Create a result entry that indicates failure
            failure_result = {
                'subject_id': subject_id,
                'success': False,
                'error_code': e.error_code,
                'error_message': e.message,
                'alpha': None,
                'xmin': None,
                'D': None,
                'p_value': None,
                'R_vs_exponential': None,
                'p_vs_exponential': None,
                'n_points': None
            }
            results.append(failure_result)
            failed_count += 1
        except Exception as e:
            # Unexpected error - log and continue
            logger.error(f"Unexpected error for {subject_id}: {str(e)}")
            failure_result = {
                'subject_id': subject_id,
                'success': False,
                'error_code': "UNEXPECTED_ERROR",
                'error_message': str(e),
                'alpha': None,
                'xmin': None,
                'D': None,
                'p_value': None,
                'R_vs_exponential': None,
                'p_vs_exponential': None,
                'n_points': None
            }
            results.append(failure_result)
            failed_count += 1
    
    logger.info(f"Fitting pipeline complete: {success_count} successful, {failed_count} failed")
    
    # Generate report
    report_path = generate_fitting_report(results, output_dir)
    
    return results, report_path

def main():
    """Main entry point for the fitting pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run power-law fitting pipeline")
    parser.add_argument("--subjects", type=str, help="Comma-separated list of subject IDs")
    parser.add_argument("--output-dir", type=str, help="Output directory for results")
    
    args = parser.parse_args()
    
    # Load subject IDs from config or command line
    if args.subjects:
        subject_ids = [s.strip() for s in args.subjects.split(',')]
    else:
        # Default: try to load from a file or use all available subjects
        data_root = get_data_root()
        avalanche_dir = Path(data_root) / "processed" / "avalanches"
        if avalanche_dir.exists():
            subject_ids = [f.stem.replace('_avalanche_sizes', '') for f in avalanche_dir.glob('*_avalanche_sizes.csv')]
        else:
            logger.warning("No avalanche data directory found. Please specify --subjects.")
            return
    
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    results, report_path = run_fitting_pipeline(subject_ids, output_dir)
    
    # Print summary
    print(f"Fitting pipeline complete.")
    print(f"Results saved to: {report_path}")
    print(f"Total subjects: {len(subject_ids)}")
    print(f"Successful: {sum(1 for r in results if r.get('success', False))}")
    print(f"Failed: {sum(1 for r in results if not r.get('success', False))}")

if __name__ == "__main__":
    main()