"""Evaluation module for llmXive pipeline."""
from .init_env_logic import verify_alfworld_environment, run_alfworld_dry_run
from .runner import check_memory_usage, load_synthesized_adapter, apply_lora_to_model, execute_environment_logic, run_evaluation, main
from .stats import load_evaluation_results, extract_success_rates, perform_paired_test, apply_benjamini_hochberg, compare_strategies, save_statistics_report, main
from .verify_memory_footprint import get_memory_usage, load_gguf_model, run_dry_run_inference, verify_memory_footprint, main
from .report_generator import load_json_safe, aggregate_results, main
from .run_sensitivity_sweep import run_sensitivity_sweep, main

__all__ = [
    "verify_alfworld_environment",
    "run_alfworld_dry_run",
    "check_memory_usage",
    "load_synthesized_adapter",
    "apply_lora_to_model",
    "execute_environment_logic",
    "run_evaluation",
    "load_evaluation_results",
    "extract_success_rates",
    "perform_paired_test",
    "apply_benjamini_hochberg",
    "compare_strategies",
    "save_statistics_report",
    "get_memory_usage",
    "load_gguf_model",
    "run_dry_run_inference",
    "verify_memory_footprint",
    "load_json_safe",
    "aggregate_results",
    "run_sensitivity_sweep",
]
