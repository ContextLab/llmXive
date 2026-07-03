"""
Features module initialization.
"""
from .extraction import define_generic_roi_grid, get_roi_annotations_fallback, calculate_fixation_in_roi
from .extraction import calculate_saccade_amplitude, calculate_dispersion, extract_face_features
from .extraction import process_participant_record, main as extraction_main
from .classification import calculate_continuous_ratio, perform_kmeans_clustering
from .classification import perform_bootstrap_stability_check, save_ratio_features, main as classification_main
from .sensitivity_clustering import perform_sensitivity_clustering, save_clustering_results, main as sensitivity_main

__all__ = [
    'define_generic_roi_grid', 'get_roi_annotations_fallback', 'calculate_fixation_in_roi',
    'calculate_saccade_amplitude', 'calculate_dispersion', 'extract_face_features',
    'process_participant_record', 'extraction_main',
    'calculate_continuous_ratio', 'perform_kmeans_clustering',
    'perform_bootstrap_stability_check', 'save_ratio_features', 'classification_main',
    'perform_sensitivity_clustering', 'save_clustering_results', 'sensitivity_main'
]