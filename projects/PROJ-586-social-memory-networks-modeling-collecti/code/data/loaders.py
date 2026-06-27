"""
Dataset loaders for social memory network experiments.

This module provides dataset loading functionality with synthetic fallback.
Since external datasets (Hanabi, CoQA) lack verified programmatic access,
all data generation falls back to the synthetic data generator.

The loader interface supports:
- Loading from CSV files
- Generating synthetic datasets
- Mixed loading (try real, fall back to synthetic)
"""

import os
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

import numpy as np
import pandas as pd

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


class DatasetLoader:
    """
    Unified dataset loader with synthetic fallback.

    This class provides a consistent interface for loading datasets,
    automatically falling back to synthetic generation when external
    data sources are unavailable.
    """

    def __init__(
        self,
        data_dir: str = "data",
        default_seed: int = 42,
        synthetic_fallback: bool = True
    ):
        """
        Initialize the dataset loader.

        Args:
            data_dir: Directory for data files.
            default_seed: Default random seed for reproducibility.
            synthetic_fallback: Whether to fall back to synthetic data
                when external sources are unavailable.
        """
        self.data_dir = Path(data_dir)
        self.default_seed = default_seed
        self.synthetic_fallback = synthetic_fallback

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_from_csv(
        self,
        filepath: Union[str, Path],
        game_id_column: str = 'game_id'
    ) -> List[Dict[str, Any]]:
        """
        Load game data from a CSV file.

        Args:
            filepath: Path to the CSV file.
            game_id_column: Column name for game identifiers.

        Returns:
            List of game data dictionaries.

        Raises:
            FileNotFoundError: If file doesn't exist and synthetic fallback
                is disabled.
        """
        filepath = Path(filepath)

        if not filepath.exists():
            if self.synthetic_fallback:
                # Generate synthetic data as fallback
                return self._generate_fallback_data(filepath.stem)
            else:
                raise FileNotFoundError(
                    f"Dataset file not found: {filepath}. "
                    "Enable synthetic_fallback to generate synthetic data."
                )

        return load_games_from_csv(str(filepath))

    def _generate_fallback_data(
        self,
        dataset_name: str
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic data as fallback.

        Args:
            dataset_name: Name of the dataset (used for seed generation).

        Returns:
            List of game data dictionaries.
        """
        # Generate deterministic seed from dataset name
        seed = hash(dataset_name) % (2**31)
        generator = SyntheticDataGenerator(seed=seed)

        # Generate 100 games with 5 agents
        games = generator.generate_dataset(
            num_games=100,
            num_agents=5,
            context_conditions=['full'],
            num_items_per_game=50,
            num_turns_per_game=200
        )

        # Convert to dictionaries
        return [
            {
                'game_id': g.game_id,
                'num_agents': g.num_agents,
                'context_condition': g.context_condition,
                'context_window_size': g.context_window_size,
                'specialization_index': g.specialization_index,
                'retrieval_efficiency': g.retrieval_efficiency,
                'total_turns': g.total_turns,
                'num_memory_items': len(g.memory_items),
            }
            for g in games
        ]

    def generate_synthetic(
        self,
        num_games: int = 100,
        num_agents: int = 5,
        context_condition: str = 'full',
        num_items_per_game: int = 50,
        num_turns_per_game: int = 200,
        seed: Optional[int] = None,
        output_path: Optional[Union[str, Path]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a synthetic dataset.

        Args:
            num_games: Number of games to generate.
            num_agents: Number of agents per game.
            context_condition: 'full' or 'limited' context.
            num_items_per_game: Memory items per game.
            num_turns_per_game: Conversation turns per game.
            seed: Random seed (uses default_seed if None).
            output_path: Optional path to save CSV output.

        Returns:
            List of game data dictionaries.
        """
        if seed is None:
            seed = self.default_seed

        generator = SyntheticDataGenerator(seed=seed)
        context_conditions = [context_condition]

        games = generator.generate_dataset(
            num_games=num_games,
            num_agents=num_agents,
            context_conditions=context_conditions,
            num_items_per_game=num_items_per_game,
            num_turns_per_game=num_turns_per_game
        )

        # Convert to dictionaries
        data = [
            {
                'game_id': g.game_id,
                'num_agents': g.num_agents,
                'context_condition': g.context_condition,
                'context_window_size': g.context_window_size,
                'specialization_index': g.specialization_index,
                'retrieval_efficiency': g.retrieval_efficiency,
                'total_turns': g.total_turns,
                'num_memory_items': len(g.memory_items),
            }
            for g in games
        ]

        # Save if output path specified
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            save_games_to_csv(games, str(output_path))

        return data

    def load_or_generate(
        self,
        dataset_name: str,
        num_games: int = 100,
        num_agents: int = 5,
        context_condition: str = 'full',
        seed: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Load dataset if exists, otherwise generate synthetic data.

        Args:
            dataset_name: Name of the dataset.
            num_games: Number of games if generating.
            num_agents: Number of agents if generating.
            context_condition: Context condition if generating.
            seed: Random seed if generating.

        Returns:
            List of game data dictionaries.
        """
        expected_path = self.data_dir / f"{dataset_name}.csv"

        if expected_path.exists():
            return self.load_from_csv(expected_path)
        else:
            return self.generate_synthetic(
                num_games=num_games,
                num_agents=num_agents,
                context_condition=context_condition,
                seed=seed,
                output_path=expected_path
            )


def get_dataset(
    name: str,
    num_games: int = 100,
    num_agents: int = 5,
    context_condition: str = 'full',
    seed: int = 42,
    data_dir: str = "data"
) -> pd.DataFrame:
    """
    Convenience function to get a dataset.

    Args:
        name: Dataset name ('baseline', 'limited', or custom).
        num_games: Number of games.
        num_agents: Number of agents.
        context_condition: Context condition.
        seed: Random seed.
        data_dir: Data directory path.

    Returns:
        DataFrame with game data.
    """
    loader = DatasetLoader(data_dir=data_dir, default_seed=seed)

    if name == 'baseline':
        data = generate_baseline_dataset(
            num_games=num_games,
            num_agents=num_agents,
            seed=seed
        )
    elif name == 'limited':
        data = generate_limited_context_dataset(
            num_games=num_games,
            num_agents=num_agents,
            seed=seed
        )
    else:
        data = loader.generate_synthetic(
            num_games=num_games,
            num_agents=num_agents,
            context_condition=context_condition,
            seed=seed
        )

    # Convert to DataFrame if list of dicts
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return pd.DataFrame(data)
    elif isinstance(data, list) and data and isinstance(data[0], GameResult):
        records = [
            {
                'game_id': g.game_id,
                'num_agents': g.num_agents,
                'context_condition': g.context_condition,
                'context_window_size': g.context_window_size,
                'specialization_index': g.specialization_index,
                'retrieval_efficiency': g.retrieval_efficiency,
                'total_turns': g.total_turns,
                'num_memory_items': len(g.memory_items),
            }
            for g in data
        ]
        return pd.DataFrame(records)
    else:
        return pd.DataFrame(data)


def load_experiment_results(
    results_path: Union[str, Path],
    required_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load experiment results from CSV.

    Args:
        results_path: Path to results CSV file.
        required_columns: Optional list of required columns to validate.

    Returns:
        DataFrame with experiment results.

    Raises:
        ValueError: If required columns are missing.
    """
    df = pd.read_csv(results_path)

    if required_columns:
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise ValueError(
                f"Missing required columns: {missing}. "
                f"Available columns: {list(df.columns)}"
            )

    return df


def save_experiment_results(
    df: pd.DataFrame,
    output_path: Union[str, Path]
) -> None:
    """
    Save experiment results to CSV.

    Args:
        df: DataFrame with results.
        output_path: Path to output CSV file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


# Module-level constants for dataset specifications
DEFAULT_NUM_GAMES = 100
DEFAULT_NUM_AGENTS = 5
DEFAULT_CONTEXT_CONDITION = 'full'
DEFAULT_NUM_ITEMS = 50
DEFAULT_NUM_TURNS = 200
DEFAULT_SEED = 42

# Dataset specification templates
DATASET_SPECS = {
    'baseline': {
        'num_games': 100,
        'num_agents': 5,
        'context_condition': 'full',
        'num_items': 50,
        'num_turns': 200,
    },
    'limited': {
        'num_games': 100,
        'num_agents': 5,
        'context_condition': 'limited',
        'num_items': 50,
        'num_turns': 200,
    },
    'scaling': {
        'num_games': 800,
        'num_agents': [3, 5, 7],
        'context_condition': 'full',
        'num_items': 50,
        'num_turns': 200,
    },
}


def get_dataset_spec(name: str) -> Dict[str, Any]:
    """
    Get dataset specification by name.

    Args:
        name: Dataset specification name.

    Returns:
        Dataset specification dictionary.

    Raises:
        KeyError: If spec name not found.
    """
    if name not in DATASET_SPECS:
        raise KeyError(
            f"Unknown dataset spec: {name}. "
            f"Available specs: {list(DATASET_SPECS.keys())}"
        )
    return DATASET_SPECS[name].copy()


def generate_all_datasets(
    data_dir: str = "data",
    seed: int = 42
) -> Dict[str, str]:
    """
    Generate all standard datasets.

    Args:
        data_dir: Directory for generated data.
        seed: Random seed.

    Returns:
        Dictionary mapping dataset name to file path.
    """
    loader = DatasetLoader(data_dir=data_dir, default_seed=seed)
    generated = {}

    # Generate baseline dataset
    baseline_path = Path(data_dir) / "baseline.csv"
    loader.generate_synthetic(
        num_games=100,
        num_agents=5,
        context_condition='full',
        seed=seed,
        output_path=baseline_path
    )
    generated['baseline'] = str(baseline_path)

    # Generate limited context dataset
    limited_path = Path(data_dir) / "limited.csv"
    loader.generate_synthetic(
        num_games=100,
        num_agents=5,
        context_condition='limited',
        seed=seed,
        output_path=limited_path
    )
    generated['limited'] = str(limited_path)

    return generated
