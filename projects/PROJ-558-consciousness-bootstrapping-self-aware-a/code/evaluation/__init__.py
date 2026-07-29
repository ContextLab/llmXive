"""
Evaluation package for the Consciousness Bootstrapping project.
Contains metrics, benchmark runners, and result schemas.
"""
from .loss_functions import compute_self_consistency_proxy, compute_joint_loss, compute_self_consistency_loss
from .metrics import (
    calculate_self_consistency,
    calculate_roc_auc,
    calculate_brier_score,
    calculate_ece,
    calculate_calibration_curve,
    calculate_entropy,
    aggregate_metrics,
    calculate_error_detection_calibration,
    save_calibration_results,
    main
)
from .results import EvaluationResult
from .run_benchmarks import (
    set_seed,
    load_model_and_tokenizer,
    prepare_gsm8k_prompt,
    prepare_mmlu_prompt,
    generate_reasoning_path,
    run_gsm8k_benchmark,
    run_mmlu_benchmark,
    create_shuffled_attention_control_dataset,
    validate_evaluation_result_schema,
    main
)

__all__ = [
    "compute_self_consistency_proxy",
    "compute_joint_loss",
    "compute_self_consistency_loss",
    "calculate_self_consistency",
    "calculate_roc_auc",
    "calculate_brier_score",
    "calculate_ece",
    "calculate_calibration_curve",
    "calculate_entropy",
    "aggregate_metrics",
    "calculate_error_detection_calibration",
    "save_calibration_results",
    "EvaluationResult",
    "set_seed",
    "load_model_and_tokenizer",
    "prepare_gsm8k_prompt",
    "prepare_mmlu_prompt",
    "generate_reasoning_path",
    "run_gsm8k_benchmark",
    "run_mmlu_benchmark",
    "create_shuffled_attention_control_dataset",
    "validate_evaluation_result_schema"
]
