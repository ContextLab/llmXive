"""
Generic grid loader for parameter sweeps.

This module provides utilities to consume parameter grids (theta, density, etc.)
and yield configuration dictionaries for simulation runs.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Generator, Union, Optional

from utils.config import get_project_paths

logger = logging.getLogger(__name__)


def load_grid_from_file(grid_path: Union[str, Path]) -> Dict[str, List[Any]]:
    """
    Load a parameter grid from a JSON file.

    Args:
        grid_path: Path to the JSON file containing the grid definition.

    Returns:
        A dictionary where keys are parameter names and values are lists of values.

    Raises:
        FileNotFoundError: If the grid file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        ValueError: If the grid structure is invalid.
    """
    path = Path(grid_path)
    if not path.exists():
        raise FileNotFoundError(f"Grid file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        grid_data = json.load(f)

    if not isinstance(grid_data, dict):
        raise ValueError(f"Grid file must contain a JSON object, got {type(grid_data)}")

    for key, values in grid_data.items():
        if not isinstance(values, list):
            raise ValueError(f"Grid parameter '{key}' must be a list of values, got {type(values)}")

    logger.info(f"Loaded grid from {path} with parameters: {list(grid_data.keys())}")
    return grid_data


def generate_grid_combinations(grid: Dict[str, List[Any]]) -> Generator[Dict[str, Any], None, None]:
    """
    Generate all combinations of parameters from a grid.

    This function performs a Cartesian product of all parameter values.

    Args:
        grid: A dictionary where keys are parameter names and values are lists of values.

    Yields:
        Dictionaries representing each unique combination of parameters.
    """
    if not grid:
        yield {}
        return

    param_names = list(grid.keys())
    param_values = [grid[name] for name in param_names]

    def cartesian_product_recursive(index: int, current: Dict[str, Any]):
        if index == len(param_names):
            yield current.copy()
            return

        name = param_names[index]
        for value in param_values[index]:
            current[name] = value
            yield from cartesian_product_recursive(index + 1, current)
            del current[name]

    yield from cartesian_product_recursive(0, {})


def load_and_yield_configs(grid_path: Union[str, Path]) -> Generator[Dict[str, Any], None, None]:
    """
    Load a grid from file and yield all configuration combinations.

    This is a convenience function that combines loading and combination generation.

    Args:
        grid_path: Path to the JSON file containing the grid definition.

    Yields:
        Dictionaries representing each unique configuration.
    """
    grid = load_grid_from_file(grid_path)
    yield from generate_grid_combinations(grid)


def create_default_theta_grid(
    theta_min: float = 0.5,
    theta_max: float = 4.0,
    theta_steps: int = 15,
    n_values: List[int] = [500, 1000, 2000],
    seeds: List[int] = [123, 456, 789]
) -> Dict[str, List[Any]]:
    """
    Create a default grid for theta sweep experiments.

    Args:
        theta_min: Minimum theta value.
        theta_max: Maximum theta value.
        theta_steps: Number of theta values to generate.
        n_values: List of matrix dimensions to test.
        seeds: List of random seeds to use.

    Returns:
        A grid dictionary with 'theta', 'N', and 'seed' parameters.
    """
    import numpy as np

    theta_values = np.linspace(theta_min, theta_max, theta_steps).tolist()

    grid = {
        'theta': theta_values,
        'N': n_values,
        'seed': seeds
    }

    logger.info(f"Created default theta grid with {len(theta_values)} theta values, "
               f"{len(n_values)} N values, and {len(seeds)} seeds.")
    return grid


def create_default_density_grid(
    densities: List[float] = [0.1, 0.2, 0.3, 0.4, 0.5],
    rank: int = 1,
    perturbation_types: List[str] = ['diagonal', 'block-sparse', 'random-sparse'],
    seeds: List[int] = [123, 456, 789]
) -> Dict[str, List[Any]]:
    """
    Create a default grid for density sensitivity analysis.

    Args:
        densities: List of support density values.
        rank: Rank of the perturbation.
        perturbation_types: List of perturbation types to test.
        seeds: List of random seeds to use.

    Returns:
        A grid dictionary with 'density', 'rank', 'type', and 'seed' parameters.
    """
    grid = {
        'density': densities,
        'rank': [rank],
        'type': perturbation_types,
        'seed': seeds
    }

    logger.info(f"Created default density grid with {len(densities)} density values, "
               f"{len(perturbation_types)} types, and {len(seeds)} seeds.")
    return grid


def main():
    """
    Command-line interface for testing the grid loader.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Test grid loader functionality')
    parser.add_argument('--grid-file', type=str, help='Path to grid JSON file')
    parser.add_argument('--create-theta', action='store_true', help='Create and print default theta grid')
    parser.add_argument('--create-density', action='store_true', help='Create and print default density grid')
    parser.add_argument('--theta-min', type=float, default=0.5, help='Min theta for default grid')
    parser.add_argument('--theta-max', type=float, default=4.0, help='Max theta for default grid')
    parser.add_argument('--theta-steps', type=int, default=15, help='Number of theta steps')
    parser.add_argument('--n-values', type=int, nargs='+', default=[500, 1000, 2000], help='N values for theta grid')
    parser.add_argument('--seeds', type=int, nargs='+', default=[123, 456, 789], help='Seeds for grid')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.create_theta:
        grid = create_default_theta_grid(
            theta_min=args.theta_min,
            theta_max=args.theta_max,
            theta_steps=args.theta_steps,
            n_values=args.n_values,
            seeds=args.seeds
        )
        print("Theta Grid:")
        print(json.dumps(grid, indent=2))
        print(f"\nTotal combinations: {sum(1 for _ in generate_grid_combinations(grid))}")

    elif args.create_density:
        grid = create_default_density_grid(seeds=args.seeds)
        print("Density Grid:")
        print(json.dumps(grid, indent=2))
        print(f"\nTotal combinations: {sum(1 for _ in generate_grid_combinations(grid))}")

    elif args.grid_file:
        try:
            configs = list(load_and_yield_configs(args.grid_file))
            print(f"Loaded {len(configs)} configurations from {args.grid_file}")
            print("\nFirst 5 configurations:")
            for i, config in enumerate(configs[:5]):
                print(f"  {i+1}: {config}")
        except Exception as e:
            logger.error(f"Failed to load grid: {e}")
            raise

    else:
        parser.print_help()


if __name__ == '__main__':
    main()