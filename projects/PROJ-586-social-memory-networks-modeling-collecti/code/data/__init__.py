"""
Data module for Social Memory Networks.
Provides dataset loaders and synthetic data generation.
"""
from .loaders import (
    DatasetLoader,
    get_dataset,
    load_experiment_results,
    save_experiment_results,
    get_dataset_spec,
    generate_all_datasets
)
from .synthetic import (
    SyntheticGameConfig,
    generate_synthetic_games,
    generate_all_datasets
)
