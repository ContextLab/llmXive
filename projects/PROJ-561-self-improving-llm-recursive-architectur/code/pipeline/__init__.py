"""
Pipeline module initialization.
"""
from .loader import (
    exponential_backoff,
    load_openwebtext,
    load_gsm8k,
    load_arc_challenge,
    load_wikitext2,
    load_all_datasets
)
from .evaluator import (
    VerificationGate,
    compute_gsm8k_accuracy,
    compute_arc_challenge_accuracy,
    compute_wikitext2_ece,
    run_all_benchmarks
)
from .model import (
    load_gpt_124m,
    get_model_param_count,
    inspect_model_structure,
    apply_weight_manipulation,
    save_model_state,
    load_model_state,
    get_modification_history,
    validate_modification_distinctness,
    apply_architectural_modification,
    compute_and_record_flops,
    aggregate_flops_over_cycles,
    generate_modification_proposal,
    enforce_distinct_modification_constraint
)
from .stats import (
    exponential_decay,
    fit_exponential_decay,
    detect_plateau_or_degradation,
    paired_bootstrap_test,
    save_bootstrap_results,
    save_decay_fit_results
)
from .trainer import (
    run_training_cycle_with_timeout,
    count_flops,
    train_epoch,
    run_training_cycle,
    get_model_param_count
)
from .memory import (
    get_memory_usage_gb,
    check_and_terminate_if_exceeds,
    enable_gradient_checkpointing,
    auto_scale_batch_size,
    run_epoch_with_memory_monitoring,
    MemoryWatchdog,
    enforce_ram_limit
)

__all__ = [
    # Loader
    'exponential_backoff',
    'load_openwebtext',
    'load_gsm8k',
    'load_arc_challenge',
    'load_wikitext2',
    'load_all_datasets',
    # Evaluator
    'VerificationGate',
    'compute_gsm8k_accuracy',
    'compute_arc_challenge_accuracy',
    'compute_wikitext2_ece',
    'run_all_benchmarks',
    # Model
    'load_gpt_124m',
    'get_model_param_count',
    'inspect_model_structure',
    'apply_weight_manipulation',
    'save_model_state',
    'load_model_state',
    'get_modification_history',
    'validate_modification_distinctness',
    'apply_architectural_modification',
    'compute_and_record_flops',
    'aggregate_flops_over_cycles',
    'generate_modification_proposal',
    'enforce_distinct_modification_constraint',
    # Stats
    'exponential_decay',
    'fit_exponential_decay',
    'detect_plateau_or_degradation',
    'paired_bootstrap_test',
    'save_bootstrap_results',
    'save_decay_fit_results',
    # Trainer
    'run_training_cycle_with_timeout',
    'count_flops',
    'train_epoch',
    'run_training_cycle',
    # Memory
    'get_memory_usage_gb',
    'check_and_terminate_if_exceeds',
    'enable_gradient_checkpointing',
    'auto_scale_batch_size',
    'run_epoch_with_memory_monitoring',
    'MemoryWatchdog',
    'enforce_ram_limit',
]