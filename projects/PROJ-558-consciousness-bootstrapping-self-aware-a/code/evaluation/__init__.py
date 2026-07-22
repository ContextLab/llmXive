"""
Evaluation package for Consciousness Bootstrapping.
Exports: EvaluationResult, compute_joint_loss, compute_self_consistency_loss,
         set_seed, load_model_and_tokenizer, prepare_gsm8k_prompt, prepare_mmlu_prompt,
         generate_reasoning_path, run_gsm8k_benchmark, run_mmlu_benchmark,
         create_shuffled_attention_control_dataset, validate_evaluation_result_schema, main
"""
from .results import EvaluationResult
from .loss_functions import compute_joint_loss, compute_self_consistency_loss
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
    main,
)

__all__ = [
    "EvaluationResult",
    "compute_joint_loss",
    "compute_self_consistency_loss",
    "set_seed",
    "load_model_and_tokenizer",
    "prepare_gsm8k_prompt",
    "prepare_mmlu_prompt",
    "generate_reasoning_path",
    "run_gsm8k_benchmark",
    "run_mmlu_benchmark",
    "create_shuffled_attention_control_dataset",
    "validate_evaluation_result_schema",
    "main",
]
