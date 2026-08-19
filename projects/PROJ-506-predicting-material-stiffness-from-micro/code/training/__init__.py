# training package
"""
Package for model training, validation, and checkpointing.
Includes CNN architecture definitions, training loops, k-fold utilities,
and data loading for microstructure datasets.
"""
from .model import StiffnessPredictorCNN, create_model
from .train import load_dataset, train_epoch, validate_epoch, train_model, save_model, main as train_main
from .kfold_utils import load_dataset_metadata, create_stratification_bins, create_combined_stratification, stratified_k_fold_split, get_fold_sizes, main as kfold_main
from .data_loader import MicrostructureDataset, MicrostructureDataLoader, main as loader_main
from .stability_report import load_fold_results, calculate_stability_metrics, append_to_report, main as stability_main

__all__ = [
    "StiffnessPredictorCNN",
    "create_model",
    "load_dataset",
    "train_epoch",
    "validate_epoch",
    "train_model",
    "save_model",
    "load_dataset_metadata",
    "create_stratification_bins",
    "create_combined_stratification",
    "stratified_k_fold_split",
    "get_fold_sizes",
    "MicrostructureDataset",
    "MicrostructureDataLoader",
    "load_fold_results",
    "calculate_stability_metrics",
    "append_to_report",
]
