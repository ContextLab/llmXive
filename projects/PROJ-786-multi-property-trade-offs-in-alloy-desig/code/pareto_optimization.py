import os
import sys
import logging
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from deap import base, creator, tools, algorithms
from scipy.spatial import ConvexHull

from config import load_environment, parse_cli_args, get_config, verify_config
from utils.logging_config import get_logger, log_warning_with_context, log_info_with_context
from utils.convex_hull import compute_convex_hull, test_points_in_hull
from model_utils import clamp_predictions, test_extrapolation, process_model_predictions

# Initialize logger
logger = get_logger(__name__)

# Global timeout configuration (seconds)
# Default 300s (5 minutes) for NSGA-II convergence check
DEFAULT_TIMEOUT = 300

def load_encoded_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Load the encoded alloy data from the processed CSV."""
    data_path = Path(config.get("data_processed_path", "data/processed/encoded_alloys.csv"))
    if not data_path.exists():
        raise FileNotFoundError(f"Encoded data not found at {data_path}")
    
    logger.info(f"Loading encoded data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Validate required columns
    required_cols = ['composition_vector'] + [f'prop_{i}' for i in range(2)] # Placeholder check, actual columns depend on encoder
    # Based on T013/T020 context, we expect Bulk and Shear columns. 
    # Assuming the encoder output has specific feature columns and target columns.
    # We need to identify the feature columns (compositional) and target columns (moduli).
    # For this script, we assume the model training step saved the feature matrix X and targets y.
    # However, the task is to generate synthetic points. We need the feature space bounds.
    
    # Let's assume the encoded data has columns for features (e.g., elemental fractions + descriptors)
    # and we need to know which columns are the features for the convex hull.
    # The previous task T023 mentions generating synthetic points within the convex hull.
    # We need to load the X matrix used for training.
    
    # For this implementation, we assume the 'encoded_alloys.csv' contains:
    # - Feature columns (all numeric columns except targets)
    # - Target columns (Bulk, Shear) - though for synthetic generation we use the model to predict these.
    # We need the feature matrix to build the convex hull.
    
    # Let's filter numeric columns for the hull
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Assuming last two columns are targets if they exist, or specific names.
    # Let's be generic: assume all numeric cols are features for the hull, 
    # and we will predict targets using the models.
    
    if len(numeric_cols) < 2:
        raise ValueError("Not enough numeric feature columns to build a convex hull.")
    
    logger.info(f"Using {len(numeric_cols)} feature columns for convex hull generation: {numeric_cols[:5]}...")
    return df, numeric_cols

def load_models(config: Dict[str, Any]) -> Tuple[Any, Any]:
    """Load the trained GradientBoosting models for Bulk and Shear moduli."""
    model_path = Path(config.get("models_path", "data/processed/models.json")) # Assuming models are saved here or similar
    # Actually, T020 saves models. Let's assume a standard path or read from config.
    # Since we don't have the exact save path from T020 in the prompt, we'll assume a standard location.
    # If T020 saves to 'data/processed/bulk_model.pkl' and 'data/processed/shear_model.pkl'
    bulk_model_path = Path(config.get("bulk_model_path", "data/processed/bulk_model.pkl"))
    shear_model_path = Path(config.get("shear_model_path", "data/processed/shear_model.pkl"))
    
    if not bulk_model_path.exists() or not shear_model_path.exists():
        raise FileNotFoundError(f"Models not found. Expected at {bulk_model_path} and {shear_model_path}")
    
    import joblib
    bulk_model = joblib.load(bulk_model_path)
    shear_model = joblib.load(shear_model_path)
    
    logger.info("Loaded Bulk and Shear models successfully")
    return bulk_model, shear_model

def generate_synthetic_points(X: np.ndarray, n_samples: int = 1000, seed: int = 42) -> np.ndarray:
    """
    Generate synthetic points within the convex hull of the training data X.
    Uses barycentric coordinates relative to the convex hull vertices.
    """
    logger.info(f"Generating {n_samples} synthetic points within the convex hull...")
    
    hull = ConvexHull(X)
    vertices = X[hull.vertices]
    
    # To generate points inside the hull, we can use the fact that any point in the hull
    # is a convex combination of the vertices.
    # However, simply averaging random vertices might not cover the volume well.
    # A better approach for DEAP is to define bounds based on the min/max of X,
    # and then reject points outside the hull.
    
    min_vals = X.min(axis=0)
    max_vals = X.max(axis=0)
    
    synthetic_points = []
    count = 0
    max_attempts = n_samples * 10  # Prevent infinite loops
    
    while len(synthetic_points) < n_samples and count < max_attempts:
        # Sample a random point in the bounding box
        point = np.random.uniform(min_vals, max_vals)
        
        # Check if point is inside the convex hull
        # Using Delaunay for point-in-hull check is robust
        if test_points_in_hull(X, np.array([point]))[0]:
            synthetic_points.append(point)
        
        count += 1
    
    if len(synthetic_points) < n_samples:
        logger.warning(f"Only generated {len(synthetic_points)} points within the convex hull after {max_attempts} attempts.")
    
    return np.array(synthetic_points)

def evaluate(individual: List[float], bulk_model: Any, shear_model: Any, 
             feature_names: List[str], timeout_start: float) -> Tuple[float, float]:
    """
    Evaluate the individual (composition vector) using the trained models.
    Returns (Bulk Modulus, Shear Modulus) as objectives to maximize.
    """
    # Check timeout
    if time.time() - timeout_start > DEFAULT_TIMEOUT:
        # We cannot simply return a value, we need to signal timeout or handle it.
        # In DEAP, we usually let the algorithm run until it hits the generation limit.
        # But the task asks for a warning if incomplete.
        # We can't stop the evaluation mid-way easily without raising an exception.
        # Instead, we rely on the main loop to check timeout.
        pass

    x = np.array(individual).reshape(1, -1)
    
    # Predict
    bulk_pred = bulk_model.predict(x)[0]
    shear_pred = shear_model.predict(x)[0]
    
    # Clamp to physical limits (FR-003/FR-004 context)
    bulk_pred = max(0, bulk_pred)
    shear_pred = max(0, shear_pred)
    
    # Return negative values because DEAP minimizes by default, but we want to maximize
    return (-bulk_pred, -shear_pred)

def run_nsgaII(config: Dict[str, Any], timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """
    Run NSGA-II algorithm to find the Pareto frontier.
    Implements convergence timeout handling as per T027.
    """
    logger.info("Starting NSGA-II Pareto Optimization...")
    
    # Load data and models
    df, feature_cols = load_encoded_data(config)
    X = df[feature_cols].values
    bulk_model, shear_model = load_models(config)
    
    # Generate synthetic points to evaluate (or use the training data + synthetic)
    # T023 mentions generating synthetic points within the convex hull.
    synthetic_X = generate_synthetic_points(X, n_samples=500, seed=config.get("seed", 42))
    
    # Combine for a larger search space? Or just evaluate synthetic?
    # Usually, we evaluate the synthetic points to find the frontier in the continuous space.
    search_space = synthetic_X
    
    # Setup DEAP
    creator.create("FitnessMax", base.Fitness, weights=(1.0, 1.0)) # Maximize both
    creator.create("Individual", list, fitness=creator.FitnessMax)
    
    toolbox = base.Toolbox()
    
    # Attribute generator
    for i, _ in enumerate(feature_cols):
        toolbox.register(f"attr_{i}", np.random.uniform, search_space[:, i].min(), search_space[:, i].max())
    
    toolbox.register("individual", tools.initIterate, creator.Individual, 
                     [lambda i=i: toolbox.__getattribute__(f"attr_{i}")() for i in range(len(feature_cols))])
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    # Evaluation function with timeout check
    def eval_wrapper(individual):
        # Check timeout before evaluation
        if time.time() - start_time > timeout:
            # Return a very bad score to discourage selection, or handle via exception?
            # Returning worst possible values to effectively remove from selection
            return (-1e9, -1e9) 
        return evaluate(individual, bulk_model, shear_model, feature_cols, start_time)
    
    toolbox.register("evaluate", eval_wrapper)
    toolbox.register("mate", tools.cxSimulatedBinaryBounded, eta=20.0, low=search_space.min(axis=0), up=search_space.max(axis=0))
    toolbox.register("mutate", tools.mutPolynomialBounded, eta=20.0, low=search_space.min(axis=0), up=search_space.max(axis=0), indpb=1.0/len(feature_cols))
    toolbox.register("select", tools.selNSGA2)
    
    # Parameters
    NGEN = config.get("n_generations", 50)
    POP_SIZE = config.get("population_size", 100)
    CXPB = config.get("cx_prob", 0.9)
    MUTPB = config.get("mut_prob", 0.1)
    
    pop = toolbox.population(n=POP_SIZE)
    hof = tools.ParetoFront()
    
    start_time = time.time()
    log_info_with_context(logger, "NSGA-II", f"Starting evolution for {NGEN} generations with timeout {timeout}s")
    
    # Evolution loop
    for gen in range(NGEN):
        # Check timeout at generation start
        if time.time() - start_time > timeout:
            log_warning_with_context(logger, "NSGA-II", f"Timeout reached at generation {gen}. Algorithm terminated early.")
            break
        
        # Evaluate
        invalid_ind = [ind for ind in pop if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        # Select
        offspring = toolbox.select(pop, len(pop))
        offspring = toolbox.map(toolbox.clone, offspring)
        
        # Apply crossover and mutation
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if np.random.random() < CXPB:
                toolbox.mate(child1, child2)
            del child1.fitness.values
            del child2.fitness.values
        
        for mutant in offspring:
            if np.random.random() < MUTPB:
                toolbox.mutate(mutant)
            del mutant.fitness.values
        
        # Replace
        pop[:] = offspring
        
        # Update Hall of Fame
        hof.update(pop)
        
        # Log progress
        if (gen + 1) % 10 == 0:
            elapsed = time.time() - start_time
            log_info_with_context(logger, "NSGA-II", f"Generation {gen+1}/{NGEN}, Time: {elapsed:.2f}s, Pareto size: {len(hof)}")
    
    elapsed_total = time.time() - start_time
    completed = elapsed_total < timeout
    
    if not completed:
        log_warning_with_context(logger, "NSGA-II", f"NSGA-II did not complete within the {timeout}s timeout. Final time: {elapsed_total:.2f}s. Frontier size: {len(hof)}")
    
    # Extract results
    pareto_points = [list(ind) for ind in hof]
    pareto_objectives = [(-ind.fitness.values[0], -ind.fitness.values[1]) for ind in hof] # Convert back to positive
    
    results = {
        "pareto_frontier": pareto_points,
        "objectives": pareto_objectives,
        "generations_completed": gen + 1,
        "total_time_seconds": elapsed_total,
        "timeout_reached": not completed,
        "config": {
            "population_size": POP_SIZE,
            "generations": NGEN,
            "timeout": timeout
        }
    }
    
    logger.info(f"NSGA-II completed. Total time: {elapsed_total:.2f}s. Timeout: {not completed}. Frontier size: {len(hof)}")
    return results

def save_results(results: Dict[str, Any], config: Dict[str, Any]):
    """Save the Pareto frontier and metrics to disk."""
    output_path = Path(config.get("pareto_output_path", "data/processed/pareto_frontier.json"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Pareto frontier saved to {output_path}")

def main():
    """Main entry point for the Pareto optimization task."""
    config = load_environment()
    args = parse_cli_args()
    config.update(vars(args))
    verify_config(config)
    
    timeout = config.get("nsga2_timeout", DEFAULT_TIMEOUT)
    
    try:
        results = run_nsgaII(config, timeout=timeout)
        save_results(results, config)
    except Exception as e:
        logger.error(f"Error during NSGA-II optimization: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()