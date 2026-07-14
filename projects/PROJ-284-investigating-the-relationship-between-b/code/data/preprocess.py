import os
import subprocess
import sys
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Optional, NamedTuple
from code.logging_config import get_logger


logger = get_logger(__name__)


class PreprocessingResult(NamedTuple):
    subject_id: str
    success: bool
    motion_corrected_path: Optional[str] = None
    normalized_path: Optional[str] = None
    preprocessed_path: Optional[str] = None
    tsnr: Optional[float] = None
    motion_valid: bool = False
    error: Optional[str] = None


def get_fsl_tool_path(tool_name: str) -> Optional[str]:
    """Get path to FSL tool."""
    fsl_home = os.getenv('FSLDIR')
    if fsl_home:
        return os.path.join(fsl_home, 'bin', tool_name)
    return None


def get_afni_tool_path(tool_name: str) -> Optional[str]:
    """Get path to AFNI tool."""
    afni_home = os.getenv('AFNIDIR')
    if afni_home:
        return os.path.join(afni_home, tool_name)
    return None


def correct_motion(nifti_path: str, output_path: str) -> bool:
    """Apply motion correction using FSL mcflirt."""
    try:
        mcflirt = get_fsl_tool_path('mcflirt')
        if not mcflirt or not os.path.exists(mcflirt):
            logger.warning("FSL mcflirt not available; skipping motion correction")
            return False
        
        cmd = [mcflirt, '-in', nifti_path, '-out', output_path]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        
        if result.returncode == 0:
            logger.info(f"Motion correction successful for {nifti_path}")
            return True
        else:
            logger.error(f"Motion correction failed: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"Motion correction error: {e}")
        return False


def slice_time_correction_and_normalization(motion_corrected_path: str, output_path: str) -> bool:
    """Apply slice-time correction and normalization using AFNI."""
    try:
        tshift = get_afni_tool_path('3dTshift')
        qwarp = get_afni_tool_path('3dQwarp')
        
        if not tshift or not qwarp:
            logger.warning("AFNI tools not available; skipping slice-time correction")
            return False
        
        # Placeholder for actual AFNI commands
        logger.info(f"Slice-time correction and normalization for {motion_corrected_path}")
        return False
        
    except Exception as e:
        logger.error(f"Slice-time correction error: {e}")
        return False


def smooth_image(normalized_path: str, output_path: str, fwhm_mm: float = 6.0) -> bool:
    """Apply smoothing using FSL fslmaths."""
    try:
        fslmaths = get_fsl_tool_path('fslmaths')
        if not fslmaths or not os.path.exists(fslmaths):
            logger.warning("FSL fslmaths not available; skipping smoothing")
            return False
        
        cmd = [fslmaths, normalized_path, '-s', str(fwhm_mm), output_path]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        
        if result.returncode == 0:
            logger.info(f"Smoothing successful for {normalized_path}")
            return True
        else:
            logger.error(f"Smoothing failed: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"Smoothing error: {e}")
        return False


def calculate_tsnr(nifti_path: str) -> Optional[float]:
    """Calculate temporal signal-to-noise ratio."""
    try:
        import nibabel as nib
        img = nib.load(nifti_path)
        data = img.get_fdata()
        
        if data.ndim != 4:
            logger.warning(f"Expected 4D data, got {data.ndim}D")
            return None
        
        # Skip first few volumes (typically 5-10)
        skip_vols = 5
        data_clean = data[:, :, :, skip_vols:]
        
        # Calculate mean and std across time
        mean_signal = np.mean(data_clean, axis=3)
        std_signal = np.std(data_clean, axis=3)
        
        # tSNR = mean / std (excluding zero voxels)
        mask = mean_signal > 0
        tsnr = np.mean(mean_signal[mask] / std_signal[mask])
        
        return float(tsnr)
        
    except Exception as e:
        logger.error(f"tSNR calculation error: {e}")
        return None


def validate_motion_parameters(motion_params_path: str, threshold_mm: float = 0.5) -> bool:
    """Validate motion parameters are below threshold."""
    try:
        import numpy as np
        motion_params = np.loadtxt(motion_params_path)
        
        if motion_params.ndim == 1:
            motion_params = motion_params.reshape(-1, 1)
        
        # Check if all motion parameters are below threshold
        max_motion = np.max(np.abs(motion_params))
        
        if max_motion < threshold_mm:
            logger.info(f"Motion validation passed: max={max_motion:.4f}mm < {threshold_mm}mm")
            return True
        else:
            logger.warning(f"Motion validation failed: max={max_motion:.4f}mm >= {threshold_mm}mm")
            return False
            
    except Exception as e:
        logger.error(f"Motion validation error: {e}")
        return False


def preprocess_subject_batch(subject_ids: list, input_dir: str, output_dir: str) -> list:
    """Preprocess a batch of subjects."""
    results = []
    
    for subject_id in subject_ids:
        nifti_path = os.path.join(input_dir, f"{subject_id}_bold.nii.gz")
        
        if not os.path.exists(nifti_path):
            results.append(PreprocessingResult(
                subject_id=subject_id,
                success=False,
                error=f"NIfTI file not found: {nifti_path}"
            ))
            continue
        
        # Motion correction
        motion_corrected = os.path.join(output_dir, f"{subject_id}_motion_corrected.nii.gz")
        if not correct_motion(nifti_path, motion_corrected):
            results.append(PreprocessingResult(
                subject_id=subject_id,
                success=False,
                error="Motion correction failed"
            ))
            continue
        
        # Slice-time correction and normalization
        normalized = os.path.join(output_dir, f"{subject_id}_normalized.nii.gz")
        if not slice_time_correction_and_normalization(motion_corrected, normalized):
            results.append(PreprocessingResult(
                subject_id=subject_id,
                success=False,
                motion_corrected_path=motion_corrected,
                error="Normalization failed"
            ))
            continue
        
        # Smoothing
        smoothed = os.path.join(output_dir, f"{subject_id}_preproc.nii.gz")
        if not smooth_image(normalized, smoothed):
            results.append(PreprocessingResult(
                subject_id=subject_id,
                success=False,
                motion_corrected_path=motion_corrected,
                normalized_path=normalized,
                error="Smoothing failed"
            ))
            continue
        
        # Calculate tSNR
        tsnr = calculate_tsnr(smoothed)
        
        # Validate motion
        motion_params_path = os.path.join(output_dir, f"{subject_id}_motion.par")
        motion_valid = validate_motion_parameters(motion_params_path) if os.path.exists(motion_params_path) else False
        
        results.append(PreprocessingResult(
            subject_id=subject_id,
            success=True,
            motion_corrected_path=motion_corrected,
            normalized_path=normalized,
            preprocessed_path=smoothed,
            tsnr=tsnr,
            motion_valid=motion_valid
        ))
    
    return results


def main():
    """Main preprocessing entry point."""
    logger.info("Preprocessing pipeline started")


if __name__ == "__main__":
    import numpy as np
    main()
