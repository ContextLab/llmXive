"""
Microstate analysis module.
Handles loading templates, applying them to EEG data, and calculating GEV.
"""
import numpy as np
import os
from typing import Tuple, Optional
from code.entities import MicrostateSegmentation

def load_microstate_template(template_path: Optional[str] = None) -> np.ndarray:
    """
    Load the pre-defined literature microstate template.
    
    Args:
        template_path: Path to the .npy file. Defaults to data/templates/microstate_template.npy
    
    Returns:
        numpy.ndarray: Template array of shape (num_classes, num_channels)
    
    Raises:
        FileNotFoundError: If the template file does not exist.
    """
    if template_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(base_dir, 'data', 'templates', 'microstate_template.npy')
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Microstate template not found at {template_path}. "
                              "Ensure T016A-1 has downloaded the template.")
    
    return np.load(template_path)

def apply_microstate_template(eeg_data: np.ndarray, 
                              template: np.ndarray) -> MicrostateSegmentation:
    """
    Apply the loaded microstate template to preprocessed EEG data to assign canonical class labels.
    
    This function performs template matching (not K-means clustering) to assign
    each time point to the most similar microstate class.
    
    Args:
        eeg_data: Preprocessed EEG data of shape (num_channels, num_timepoints)
        template: Microstate template of shape (num_classes, num_channels)
    
    Returns:
        MicrostateSegmentation: Object containing labels, GEV, and metadata.
    
    Raises:
        ValueError: If data shapes are incompatible.
    """
    if eeg_data.ndim != 2:
        raise ValueError(f"EEG data must be 2D (channels, timepoints), got {eeg_data.ndim}D")
    
    if template.ndim != 2:
        raise ValueError(f"Template must be 2D (classes, channels), got {template.ndim}D")
    
    num_channels, num_timepoints = eeg_data.shape
    num_classes, template_channels = template.shape
    
    if num_channels != template_channels:
        raise ValueError(f"Channel mismatch: EEG has {num_channels}, template has {template_channels}")
    
    if num_timepoints == 0:
        raise ValueError("EEG data has 0 timepoints.")

    # Normalize template topographies (unit norm)
    template_norms = np.linalg.norm(template, axis=1, keepdims=True)
    template_normalized = template / template_norms

    # Normalize EEG data at each time point (unit norm)
    eeg_norms = np.linalg.norm(eeg_data, axis=0, keepdims=True)
    # Avoid division by zero
    eeg_norms[eeg_norms == 0] = 1.0
    eeg_normalized = eeg_data / eeg_norms

    # Calculate correlation (similarity) between each time point and each template
    # Result shape: (num_classes, num_timepoints)
    similarity_matrix = np.dot(template_normalized, eeg_normalized)

    # Assign labels: class with maximum correlation at each time point
    labels = np.argmax(similarity_matrix, axis=0)

    # Calculate Global Explained Variance (GEV)
    # GEV = Sum over classes (variance explained by class) / Total variance
    # Variance explained by class k = Sum_t (x_t - mean_k)^2 where x_t is assigned to k
    # Simplified GEV calculation using correlation squared for unit-norm data:
    # GEV = (1/N) * Sum_t (max_correlation_t)^2 * (Signal Power at t) / Total Power
    # Since we normalized, we can use the squared max correlation as a proxy for explained variance
    # More precise GEV calculation:
    
    # Reconstruct the signal using the assigned template class
    # We need the original (unnormalized) template to reconstruct amplitude?
    # Standard GEV formula: GEV = Sum_k Sum_{t in k} (x_t . t_k)^2 / Sum_t ||x_t||^2
    # where t_k is the template vector for class k (normalized), x_t is the data vector (normalized)
    # (x_t . t_k) is exactly the similarity value at time t for the assigned class
    
    # Get the max correlation for each time point
    max_correlations = np.max(similarity_matrix, axis=0)
    
    # Calculate total variance (sum of squared norms, which is N since normalized)
    total_variance = num_timepoints # Since ||x_t||^2 = 1 for all t
    
    # Calculate explained variance: sum of (max_correlation)^2
    # Note: In standard GEV, we sum (x_t . t_k)^2. Since we normalized x_t, this is just the squared correlation.
    explained_variance = np.sum(max_correlations ** 2)
    
    gev = explained_variance / total_variance
    
    # Verify GEV threshold (>= 0.75) - this is a check, not a failure condition for the function itself
    # The function returns the metric; the caller or test verifies the threshold.
    
    return MicrostateSegmentation(
        labels=labels,
        gev=gev,
        num_classes=num_classes,
        num_channels=num_channels,
        num_timepoints=num_timepoints,
        template_path=None # Path not tracked in object, but used to generate
    )

def add_associational_flag_to_microstate(segmentation: MicrostateSegmentation, metadata: dict) -> dict:
    """
    Add the analysis_type: associational metadata flag to microstate feature files.
    
    Args:
        segmentation: The MicrostateSegmentation object.
        metadata: Existing metadata dictionary.
    
    Returns:
        Updated metadata dictionary.
    """
    metadata['analysis_type'] = 'associational'
    return metadata