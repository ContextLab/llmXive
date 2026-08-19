"""
Evaluation metrics and benchmarking.
"""
from .loss_functions import compute_self_consistency_proxy, compute_joint_loss, compute_self_consistency_loss
from .metrics import calculate_self_consistency, calculate_roc_auc, calculate_brier_score, calculate_ece, calculate_calibration_curve, calculate_entropy, aggregate_metrics, calculate_error_detection_calibration, save_calibration_results, main
from .results import EvaluationResult
from .run_benchmarks import BenchmarkConfig, set_seed, load_gsm8k_dataset, load_mmlu_dataset, load_model_and_tokenizer, prepare_gsm8k_prompt, prepare_mmlu_prompt, generate_reasoning_path, parse_gsm8k_answer, parse_mmlu_answer, calculate_accuracy, run_gsm8k_benchmark, run_mmlu_benchmark, save_benchmark_results, main
from .run_calibration_script import load_evaluation_results, extract_error_data, main
