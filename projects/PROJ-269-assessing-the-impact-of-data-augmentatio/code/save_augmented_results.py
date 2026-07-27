import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Import from existing API surface
from simulation import run_full_simulation
from augment import inject_gaussian_noise, apply_smote, apply_random_oversampling, augment_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RESULTS_DIR = Path("results")
DISCLAIMER = "DISCLAIMER: Findings are associational and do not imply causation. Results are specific to the experimental conditions defined in the simulation parameters."

AUGMENTATION_METHODS = {
    'gaussian': inject_gaussian_noise,
    'smote': apply_smote,
    'random_oversampling': apply_random_oversampling
}

def save_augmented_results(
    dataset_name: str,
    dataset_path: Path,
    sample_size: int,
    method: str,
    condition: str,
    num_iterations: int = 1000,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Run simulation with augmentation and save results to JSON.

    Args:
        dataset_name: Name of the dataset (e.g., 'breast_cancer')
        dataset_path: Path to the dataset file
        sample_size: Number of samples (15, 25, or 40)
        method: Augmentation method ('gaussian', 'smote', 'random_oversampling')
        condition: Condition type ('null' or 'alt')
        num_iterations: Number of Monte Carlo iterations
        random_seed: Random seed for reproducibility

    Returns:
        Dictionary containing the simulation results
    """
    logger.info(f"Running augmented simulation: {dataset_name}, N={sample_size}, "
               f"method={method}, condition={condition}")

    if method not in AUGMENTATION_METHODS:
        raise ValueError(f"Unknown augmentation method: {method}. "
                       f"Valid methods: {list(AUGMENTATION_METHODS.keys())}")

    if condition not in ['null', 'alt']:
        raise ValueError(f"Unknown condition: {condition}. Valid: 'null', 'alt'")

    # Get augmentation function
    augment_func = AUGMENTATION_METHODS[method]

    # Run simulation with augmentation
    # The simulation module expects a function that takes (X, y) and returns (X_aug, y_aug)
    def augmentation_wrapper(X, y):
        return augment_func(X, y)

    results = run_full_simulation(
        dataset_path=dataset_path,
        sample_size=sample_size,
        condition=condition,
        augmentation_func=augmentation_wrapper,
        num_iterations=num_iterations,
        random_seed=random_seed
    )

    # Prepare output structure
    output = {
        'metadata': {
            'dataset': dataset_name,
            'sample_size': sample_size,
            'augmentation_method': method,
            'condition': condition,
            'num_iterations': num_iterations,
            'random_seed': random_seed,
            'disclaimer': DISCLAIMER
        },
        'results': results
    }

    # Save to file
    output_filename = f"{dataset_name}_{sample_size}_{method}_{condition}.json"
    output_path = RESULTS_DIR / output_filename

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info(f"Saved results to {output_path}")

    return output

def main():
    """Main entry point for running augmented simulations."""
    parser = argparse.ArgumentParser(description="Save augmented simulation results")
    parser.add_argument('--dataset', type=str, required=True,
                      help='Dataset name (e.g., breast_cancer, ionosphere, heart_disease)')
    parser.add_argument('--size', type=int, required=True,
                      choices=[15, 25, 40],
                      help='Sample size (15, 25, or 40)')
    parser.add_argument('--method', type=str, required=True,
                      choices=['gaussian', 'smote', 'random_oversampling'],
                      help='Augmentation method')
    parser.add_argument('--condition', type=str, required=True,
                      choices=['null', 'alt'],
                      help='Condition type (null or alt)')
    parser.add_argument('--iterations', type=int, default=1000,
                      help='Number of Monte Carlo iterations')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed')

    args = parser.parse_args()

    # Ensure results directory exists
    RESULTS_DIR.mkdir(exist_ok=True)

    # Construct dataset path
    dataset_path = Path("data/raw") / f"{args.dataset}.csv"
    if not dataset_path.exists():
        logger.error(f"Dataset not found: {dataset_path}")
        return

    # Run and save results
    save_augmented_results(
        dataset_name=args.dataset,
        dataset_path=dataset_path,
        sample_size=args.size,
        method=args.method,
        condition=args.condition,
        num_iterations=args.iterations,
        random_seed=args.seed
    )

if __name__ == "__main__":
    main()