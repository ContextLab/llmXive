"""
Modeling module for phylogenetic analysis and model training.
"""
from .phylo import PhylogenyError, load_phylogeny, construct_covariance_matrix, train_pgls, main
from .train import (
    StratifiedSplitError,
    ModelTrainingError,
    get_clade_members,
    find_balanced_clades,
    create_stratified_split,
    load_pca_features,
    apply_pca,
    train_models_loo,
    determine_cv_method,
    train_models_5fold,
    main as train_main,
)
from .eval import (
    load_model_results,
    save_metrics,
    evaluate_models,
    run_phylogenetic_permutation,
    calculate_significance,
    report_primary_results,
    retrain_with_thresholds,
    run_sensitivity_sweep,
    calculate_variation,
    main as eval_main,
)
