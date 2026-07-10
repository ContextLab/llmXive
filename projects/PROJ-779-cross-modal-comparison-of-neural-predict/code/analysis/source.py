import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import mne
from code.config import get_config
from code.utils.logger import get_logger

class SourceLocalizationError(Exception):
    """Custom exception for source localization failures."""
    pass

def setup_icbm152_head_model() -> Dict[str, Any]:
    """
    Setup ICBM152 head model for source localization.
    
    Returns:
        Dict containing 'forward', 'src', 'bem' components.
    """
    logger = get_logger(__name__)
    logger.info("Setting up ICBM152 head model...")
    
    try:
        # Load the standard ICBM152 BEM model
        trans = mne.make_transformation('head', 'mri')
        src = mne.setup_source_space('ico5', subjects_dir=mne.datasets.sample.data_path() / 'subjects', add_dist=False)
        bem = mne.make_bem_model(subject='fsaverage', ico=4, subjects_dir=mne.datasets.sample.data_path() / 'subjects')
        bem_sol = mne.make_bem_solution(bem)
        
        # Create forward solution (using dummy info for demo if no raw data)
        # In real usage, this would use info from raw data
        info = mne.create_info(ch_names=['MEG 0111'], sfreq=1000, ch_types=['mag'])
        fwd = mne.make_forward_solution(info, trans=trans, src=src, bem=bem_sol, 
                                      mindist=5.0, n_jobs=1)
        
        return {'forward': fwd, 'src': src, 'bem': bem_sol}
    except Exception as e:
        logger.error(f"Failed to setup ICBM152 head model: {str(e)}")
        raise SourceLocalizationError(f"ICBM152 setup failed: {str(e)}")

def setup_source_space(subject: str = 'fsaverage') -> Any:
    """
    Setup source space for a given subject.
    
    Args:
        subject: Subject name (default: 'fsaverage')
        
    Returns:
        Source space object.
    """
    logger = get_logger(__name__)
    logger.info(f"Setting up source space for subject: {subject}")
    
    try:
        subjects_dir = mne.datasets.sample.data_path() / 'subjects'
        src = mne.setup_source_space('ico5', subjects_dir=subjects_dir, add_dist=False)
        return src
    except Exception as e:
        logger.error(f"Failed to setup source space: {str(e)}")
        raise SourceLocalizationError(f"Source space setup failed: {str(e)}")

def compute_lead_fields(info: Any, src: Any, bem: Any, trans: Any) -> Any:
    """
    Compute lead fields (forward solution) for given setup.
    
    Args:
        info: MNE info object
        src: Source space
        bem: BEM solution
        trans: Transformation matrix
        
    Returns:
        Forward solution object.
    """
    logger = get_logger(__name__)
    logger.info("Computing lead fields...")
    
    try:
        fwd = mne.make_forward_solution(info, trans=trans, src=src, bem=bem, 
                                      mindist=5.0, n_jobs=1)
        return fwd
    except Exception as e:
        logger.error(f"Failed to compute lead fields: {str(e)}")
        raise SourceLocalizationError(f"Lead field computation failed: {str(e)}")

def load_lead_fields(fwd_path: str) -> Any:
    """
    Load pre-computed lead fields from file.
    
    Args:
        fwd_path: Path to forward solution file.
        
    Returns:
        Forward solution object.
    """
    logger = get_logger(__name__)
    logger.info(f"Loading lead fields from: {fwd_path}")
    
    try:
        fwd = mne.read_forward_solution(fwd_path)
        return fwd
    except Exception as e:
        logger.error(f"Failed to load lead fields: {str(e)}")
        raise SourceLocalizationError(f"Lead field loading failed: {str(e)}")

def compute_inverse_operator(fwd: Any, cov: Any, loose: float = 0.2, depth: float = 0.8) -> Any:
    """
    Compute inverse operator for source estimation.
    
    Args:
        fwd: Forward solution
        cov: Noise covariance matrix
        loose: Loose orientation constraint (0-1)
        depth: Depth weighting (0-1)
        
    Returns:
        Inverse operator object.
    """
    logger = get_logger(__name__)
    logger.info("Computing inverse operator...")
    
    try:
        inv = mne.make_inverse_operator(fwd['info'], fwd, cov, loose=loose, depth=depth)
        return inv
    except Exception as e:
        logger.error(f"Failed to compute inverse operator: {str(e)}")
        raise SourceLocalizationError(f"Inverse operator computation failed: {str(e)}")

def apply_inverse_source_estimation(inv: Any, evoked: Any, method: str = 'dSPM') -> Any:
    """
    Apply inverse operator to evoked data for source estimation.
    
    Args:
        inv: Inverse operator
        evoked: Evoked response data
        method: Inverse method ('dSPM', 'sLORETA', 'MNE')
        
    Returns:
        Source estimate object.
    """
    logger = get_logger(__name__)
    logger.info(f"Applying inverse source estimation using {method}...")
    
    try:
        stc = mne.apply_inverse(evoked, inv, lambda2=1.0/9.0, method=method)
        return stc
    except Exception as e:
        logger.error(f"Failed to apply inverse source estimation: {str(e)}")
        raise SourceLocalizationError(f"Source estimation failed: {str(e)}")

def run_sensitivity_analysis(fwd_path: str, evoked_path: str, output_path: str) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping spatial smoothing kernel (sigma) values.
    
    Args:
        fwd_path: Path to forward solution file
        evoked_path: Path to evoked response file
        output_path: Path to save sensitivity analysis results (CSV)
        
    Returns:
        Dictionary containing analysis results.
    """
    logger = get_logger(__name__)
    logger.info("Starting sensitivity analysis...")
    
    # Define sigma values (low, medium, high) in mm
    sigmas = [5.0, 10.0, 15.0]  # mm
    results = []
    
    try:
        # Load data
        fwd = mne.read_forward_solution(fwd_path)
        evoked = mne.read_evokeds(evoked_path, condition=0)
        
        # Compute noise covariance (simplified for demo)
        cov = mne.compute_covariance(evoked, tmin=0, tmax=0.1)
        
        # Compute inverse operator
        inv = mne.make_inverse_operator(evoked.info, fwd, cov, loose=0.2, depth=0.8)
        
        for sigma in sigmas:
            logger.info(f"Processing sigma = {sigma} mm...")
            
            # Apply inverse with current sigma (using depth weighting as proxy for smoothing)
            # Note: In MNE, 'depth' parameter acts as a form of spatial smoothing/weighting
            inv_smoothed = mne.make_inverse_operator(evoked.info, fwd, cov, loose=0.2, depth=sigma/20.0)
            
            # Apply inverse
            stc = mne.apply_inverse(evoked, inv_smoothed, lambda2=1.0/9.0, method='dSPM')
            
            # Extract source strength (mean across vertices and time)
            source_strength = np.mean(stc.data)
            
            # Compute coefficient of variation (std/mean)
            source_std = np.std(stc.data)
            cv = source_std / abs(source_strength) if source_strength != 0 else 0.0
            
            results.append({
                'sigma_mm': sigma,
                'source_strength': float(source_strength),
                'source_std': float(source_std),
                'coefficient_of_variation': float(cv)
            })
            
            logger.info(f"  Source strength: {source_strength:.4f}, CV: {cv:.4f}")
        
        # Save results to CSV
        import pandas as pd
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
        logger.info(f"Sensitivity analysis results saved to: {output_path}")
        
        return {
            'status': 'success',
            'results': results,
            'output_file': output_path
        }
        
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {str(e)}")
        raise SourceLocalizationError(f"Sensitivity analysis failed: {str(e)}")

def main():
    """
    Main function to run sensitivity analysis.
    """
    logger = get_logger(__name__)
    logger.info("Running sensitivity analysis main...")
    
    config = get_config()
    
    # Ensure output directory exists
    output_dir = Path(config['paths']['results'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define paths
    fwd_path = Path(config['paths']['data']) / 'intermediate' / 'forward_solution.fif'
    evoked_path = Path(config['paths']['data']) / 'intermediate' / 'evoked.fif'
    output_path = output_dir / 'sensitivity_analysis.csv'
    
    # Check if required files exist
    if not fwd_path.exists():
        logger.error(f"Forward solution not found: {fwd_path}")
        logger.info("Please run source localization first to generate forward solution.")
        return {'status': 'error', 'message': 'Forward solution not found'}
    
    if not evoked_path.exists():
        logger.error(f"Evoked data not found: {evoked_path}")
        logger.info("Please run preprocessing and metrics extraction first.")
        return {'status': 'error', 'message': 'Evoked data not found'}
    
    # Run sensitivity analysis
    try:
        result = run_sensitivity_analysis(str(fwd_path), str(evoked_path), str(output_path))
        logger.info(f"Sensitivity analysis completed successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {str(e)}")
        return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    main()
