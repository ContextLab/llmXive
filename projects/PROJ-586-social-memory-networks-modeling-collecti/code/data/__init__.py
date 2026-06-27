"""
Data module for social memory network experiments.

This module provides dataset loading and generation functionality
with synthetic fallback for reproducible experiments.

Exports:
    DatasetLoader: Main loader class with synthetic fallback.
    SyntheticDataGenerator: Synthetic data generation engine.
    get_dataset: Convenience function for dataset retrieval.
    load_experiment_results: Load experiment results from CSV.
    save_experiment_results: Save experiment results to CSV.
    generate_all_datasets: Generate all standard datasets.
    GameResult: Dataclass for game simulation results.
    MemoryItem: Dataclass for memory items.
    ConversationTurn: Dataclass for conversation turns.
"""

from .loaders import (
    DatasetLoader,
    get_dataset,
    load_experiment_results,
    save_experiment_results,
    generate_all_datasets,
    DEFAULT_NUM_GAMES,
    DEFAULT_NUM_AGENTS,
    DEFAULT_CONTEXT_CONDITION,
    DEFAULT_NUM_ITEMS,
    DEFAULT_NUM_TURNS,
    DEFAULT_SEED,
    DATASET_SPECS,
    get_dataset_spec,
)

from .synthetic import (
    SyntheticDataGenerator,
    GameResult,
    MemoryItem,
    ConversationTurn,
    save_games_to_csv,
    load_games_from_csv,
    generate_baseline_dataset,
    generate_limited_context_dataset,
)

__all__ = [
    # Loader classes and functions
    'DatasetLoader',
    'get_dataset',
    'load_experiment_results',
    'save_experiment_results',
    'generate_all_datasets',
    'get_dataset_spec',

    # Constants
    'DEFAULT_NUM_GAMES',
    'DEFAULT_NUM_AGENTS',
    'DEFAULT_CONTEXT_CONDITION',
    'DEFAULT_NUM_ITEMS',
    'DEFAULT_NUM_TURNS',
    'DEFAULT_SEED',
    'DATASET_SPECS',

    # Synthetic generation
    'SyntheticDataGenerator',
    'GameResult',
    'MemoryItem',
    'ConversationTurn',
    'save_games_to_csv',
    'load_games_from_csv',
    'generate_baseline_dataset',
    'generate_limited_context_dataset',
]