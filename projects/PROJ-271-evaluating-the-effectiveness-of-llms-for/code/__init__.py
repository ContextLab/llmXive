"""
Code analysis pipeline for evaluating LLM effectiveness on code smell detection.
"""
from .config import get_path, get_data_path, get_processed_path, get_results_path, setup_logging
from .data_pipeline import load_sampled_functions, compute_radon_metrics, run_pylint_analysis, normalize_pylint_smells, process_functions, save_to_csv, validate_output, run_pipeline
from .monitoring import get_ram_usage_mb, get_cpu_utilization, get_system_ram_usage_mb, get_system_cpu_utilization, capture_snapshot, track_inference_time, record_batch_metrics, save_metrics_to_file, get_peak_ram_for_batch
from .semantic_analysis import load_embeddings_model, load_baseline_data, compute_embeddings, save_embeddings_to_csv, load_llama_model, run_llm_inference, run_semantic_analysis
from .linting_config import run_flake8_check, run_black_format, run_all_checks

__all__ = [
    'get_path', 'get_data_path', 'get_processed_path', 'get_results_path', 'setup_logging',
    'load_sampled_functions', 'compute_radon_metrics', 'run_pylint_analysis', 'normalize_pylint_smells',
    'process_functions', 'save_to_csv', 'validate_output', 'run_pipeline',
    'get_ram_usage_mb', 'get_cpu_utilization', 'get_system_ram_usage_mb', 'get_system_cpu_utilization',
    'capture_snapshot', 'track_inference_time', 'record_batch_metrics', 'save_metrics_to_file', 'get_peak_ram_for_batch',
    'load_embeddings_model', 'load_baseline_data', 'compute_embeddings', 'save_embeddings_to_csv',
    'load_llama_model', 'run_llm_inference', 'run_semantic_analysis',
    'run_flake8_check', 'run_black_format', 'run_all_checks'
]