"""
Modeling module for sleep quality prediction.
Contains training, evaluation, and interpretation logic.
"""
from .pipeline_factory import NestedCVPipeline, create_pipeline
from .train import load_data, run_training, main as train_main
from .evaluate import load_predictions, calculate_r2, bootstrap_resample_r2, save_bootstrap_results, main as evaluate_main
from .interpret import load_model_coefficients, extract_nonzero_edges, run_interpretation, main as interpret_main
from .visualize import generate_brain_plot, run_visualization_pipeline, main as visualize_main
from .report_generator import load_result_report, save_result_report, generate_result_report, finalize_report, main as report_main
from .finalize_report import verify_plot_file, finalize_report, main as finalize_main
from .validate_plot import count_svg_edges, main as validate_main

__all__ = [
    'NestedCVPipeline', 'create_pipeline',
    'load_data', 'run_training', 'train_main',
    'load_predictions', 'calculate_r2', 'bootstrap_resample_r2', 'save_bootstrap_results', 'evaluate_main',
    'load_model_coefficients', 'extract_nonzero_edges', 'run_interpretation', 'interpret_main',
    'generate_brain_plot', 'run_visualization_pipeline', 'visualize_main',
    'load_result_report', 'save_result_report', 'generate_result_report', 'finalize_report', 'report_main',
    'verify_plot_file', 'finalize_report', 'finalize_main',
    'count_svg_edges', 'validate_main'
]
