"""Modeling package for US2 and US3 tasks."""
from .evaluate import (
    load_best_models,
    load_test_data,
    evaluate_model,
    compute_per_class_metrics,
    run_evaluation,
    main,
)
from .memory_utils import (
    get_available_memory_gb,
    check_memory_limit,
    enforce_cpu_only,
    batch_dataframe,
    estimate_dataframe_memory_mb,
    validate_training_data_size,
    safe_gc,
)
from .save_models import (
    ensure_dir,
    save_model_artifacts,
    main as save_models_main,
)
from .split import (
    get_scaffold_group_keys,
    stratified_scaffold_split,
    create_train_val_test_split,
    extract_validation_set,
    main as split_main,
)
from .train import (
    load_and_prepare_data,
    train_random_forest_grid_search,
    train_svm_grid_search,
    run_memory_profiling,
    main as train_main,
)
from .train_bounded import (
    load_and_prepare_data as load_bounded,
    train_random_forest_bounded,
    train_svm_bounded,
    main as train_bounded_main,
)

__all__ = [
    "load_best_models",
    "load_test_data",
    "evaluate_model",
    "compute_per_class_metrics",
    "run_evaluation",
    "main",
    "get_available_memory_gb",
    "check_memory_limit",
    "enforce_cpu_only",
    "batch_dataframe",
    "estimate_dataframe_memory_mb",
    "validate_training_data_size",
    "safe_gc",
    "ensure_dir",
    "save_model_artifacts",
    "save_models_main",
    "get_scaffold_group_keys",
    "stratified_scaffold_split",
    "create_train_val_test_split",
    "extract_validation_set",
    "split_main",
    "load_and_prepare_data",
    "train_random_forest_grid_search",
    "train_svm_grid_search",
    "run_memory_profiling",
    "train_main",
    "load_bounded",
    "train_random_forest_bounded",
    "train_svm_bounded",
    "train_bounded_main",
]
