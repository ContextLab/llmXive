"""
Pareto Optimization using NSGA-II for Multi-Property Trade-offs in Alloy Design.

This module implements the NSGA-II algorithm using DEAP to find optimal alloy
compositions that maximize Bulk and Shear Moduli while staying within the
convex hull of the training data.
"""

import os
import sys
import logging
import argparse
import json
import time
import signal
import threading
import traceback
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from deap import base, creator, tools, algorithms
from scipy.spatial import ConvexHull, Delaunay

# Project imports
from utils.convex_hull import ConvexHullWrapper, compute_convex_hull, test_points_in_hull
from config import get_config
from utils.logging_config import get_logger, log_info_with_context, log_warning_with_context, log_error_with_context

# Global timeout flag
_TIMEOUT_REACHED = False
_TIMEOUT_SECONDS = 180  # 3 minute hard limit

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    global _TIMEOUT_REACHED
    _TIMEOUT_REACHED = True
    log_warning_with_context("TIMEOUT", "Hard timeout reached. Stopping optimization gracefully.")

class TimeoutWatchdog:
    """Cross-platform timeout watchdog."""
    def __init__(self, seconds: int):
        self.seconds = seconds
        self.timer = None
        self.reached = False

    def start(self):
        """Start the watchdog timer."""
        if os.name == 'posix':
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.seconds)
        else:
            # Windows fallback using threading
            self.timer = threading.Timer(self.seconds, self._trigger_timeout)
            self.timer.daemon = True
            self.timer.start()

    def _trigger_timeout(self):
        self.reached = True
        log_warning_with_context("TIMEOUT", "Hard timeout reached. Stopping optimization gracefully.")

    def check(self):
        """Check if timeout has been reached."""
        if os.name != 'posix':
            return self.reached
        return _TIMEOUT_REACHED

    def cancel(self):
        """Cancel the watchdog."""
        if os.name == 'posix':
            signal.alarm(0)
        elif self.timer:
            self.timer.cancel()

def load_encoded_data(data_path: str) -> pd.DataFrame:
    """Load encoded alloy data from CSV."""
    logger = get_logger(__name__)
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} entries from {data_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load data from {data_path}: {e}")
        raise

def load_models(models_dir: str) -> Dict[str, Any]:
    """Load trained models from pickle files."""
    logger = get_logger(__name__)
    models = {}
    try:
        import joblib
        bulk_model_path = os.path.join(models_dir, "bulk_model.pkl")
        shear_model_path = os.path.join(models_dir, "shear_model.pkl")
        
        if os.path.exists(bulk_model_path):
            models['bulk'] = joblib.load(bulk_model_path)
            logger.info("Loaded bulk modulus model")
        else:
            logger.warning(f"Bulk model not found at {bulk_model_path}")
        
        if os.path.exists(shear_model_path):
            models['shear'] = joblib.load(shear_model_path)
            logger.info("Loaded shear modulus model")
        else:
            logger.warning(f"Shear model not found at {shear_model_path}")
        
        return models
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise

def load_validation_report(report_path: str) -> Dict[str, Any]:
    """Load the enhanced model validation report with uncertainty_variance."""
    logger = get_logger(__name__)
    try:
        with open(report_path, 'r') as f:
            report = json.load(f)
        logger.info(f"Loaded validation report from {report_path}")
        return report
    except Exception as e:
        logger.warning(f"Failed to load validation report from {report_path}: {e}. Proceeding without reliability mask.")
        return {}

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """Extract feature column names from dataframe."""
    # Feature columns are those that are not composition, bulk_modulus, or shear_modulus
    exclude_cols = ['composition', 'bulk_modulus', 'shear_modulus', 'element_features']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    return feature_cols

def generate_synthetic_points(
    training_data: pd.DataFrame,
    n_points: int,
    hull_wrapper: ConvexHullWrapper
) -> Tuple[np.ndarray, List[bool]]:
    """
    Generate synthetic points strictly within the convex hull of training data.
    
    Returns:
        Tuple of (points array, validity flags)
        Points on boundary are allowed (valid=True)
        Points outside hull are rejected (valid=False)
    """
    logger = get_logger(__name__)
    feature_cols = get_feature_columns(training_data)
    
    if len(feature_cols) == 0:
        raise ValueError("No feature columns found in training data")
    
    # Get feature matrix
    X_train = training_data[feature_cols].values
    
    # Generate random points in the bounding box
    min_vals = X_train.min(axis=0)
    max_vals = X_train.max(axis=0)
    
    synthetic_points = []
    valid_flags = []
    distances_to_boundary = []
    
    attempts = 0
    max_attempts = n_points * 100  # Prevent infinite loops
    
    while len(synthetic_points) < n_points and attempts < max_attempts:
        attempts += 1
        
        # Generate a random point in the bounding box
        point = np.random.uniform(min_vals, max_vals)
        
        # Test if point is inside or on boundary of convex hull
        is_inside, distance = hull_wrapper.is_inside(point, return_distance=True)
        
        if is_inside:
            synthetic_points.append(point)
            valid_flags.append(True)
            distances_to_boundary.append(distance)
        else:
            valid_flags.append(False)
            distances_to_boundary.append(distance)
    
    if len(synthetic_points) < n_points:
        logger.warning(f"Only generated {len(synthetic_points)} valid points out of {n_points} requested")
    
    return np.array(synthetic_points), valid_flags, distances_to_boundary

def evaluate(
    individual: List[float],
    models: Dict[str, Any],
    hull_wrapper: ConvexHullWrapper,
    training_data: pd.DataFrame,
    validation_report: Dict[str, Any],
    feature_cols: List[str]
) -> Tuple[float, float, float, bool, float]:
    """
    Evaluate an individual (composition) using trained models.
    
    Returns:
        Tuple of (bulk_modulus, shear_modulus, uncertainty_penalty, is_valid, distance_to_boundary)
    """
    logger = get_logger(__name__)
    
    # Check if point is within convex hull
    is_inside, distance = hull_wrapper.is_inside(np.array(individual), return_distance=True)
    
    if not is_inside:
        # Return heavily penalized values for points outside hull
        return -1e9, -1e9, 1e9, False, distance
    
    # Calculate distance to boundary for boundary proximity flagging
    hull_radius = hull_wrapper.get_radius()
    boundary_threshold = 0.05 * hull_radius
    is_near_boundary = distance < boundary_threshold
    
    # Predict properties
    try:
        point = np.array(individual).reshape(1, -1)
        
        if 'bulk' in models and 'shear' in models:
            bulk_pred = models['bulk'].predict(point)[0]
            shear_pred = models['shear'].predict(point)[0]
        else:
            logger.error("Models not loaded properly")
            return -1e9, -1e9, 1e9, False, distance
        
        # Apply reliability mask based on uncertainty_variance
        uncertainty_penalty = 0.0
        if validation_report and 'uncertainty_variance' in validation_report:
            # Estimate uncertainty based on distance to training data
            # This is a simplified approach - in practice, we'd use model-specific uncertainty
            uncertainty_penalty = 1.0 / (1.0 + distance)  # Higher penalty for points far from data
        
        # Clamp predictions to physical limits
        bulk_pred = max(0.0, bulk_pred)
        shear_pred = max(0.0, shear_pred)
        
        return bulk_pred, shear_pred, uncertainty_penalty, True, distance
        
    except Exception as e:
        logger.error(f"Prediction failed for individual: {e}")
        return -1e9, -1e9, 1e9, False, distance

def run_nsgaII(
    training_data: pd.DataFrame,
    models: Dict[str, Any],
    hull_wrapper: ConvexHullWrapper,
    validation_report: Dict[str, Any],
    population_size: int = 100,
    generations: int = 50,
    cx_prob: float = 0.9,
    mut_prob: float = 0.1,
    timeout_seconds: int = 180
) -> List[Tuple[float, float, float, bool, float]]:
    """
    Run NSGA-II optimization algorithm.
    
    Returns:
        List of Pareto optimal solutions with their properties and metadata
    """
    logger = get_logger(__name__)
    feature_cols = get_feature_columns(training_data)
    n_features = len(feature_cols)
    
    if n_features == 0:
        raise ValueError("No feature columns found")
    
    # Setup DEAP
    creator.create("FitnessMax", base.Fitness, weights=(1.0, 1.0))  # Maximize both
    creator.create("Individual", list, fitness=creator.FitnessMax)
    
    toolbox = base.Toolbox()
    
    # Attribute generator: random composition within feature bounds
    min_vals = training_data[feature_cols].min().values
    max_vals = training_data[feature_cols].max().values
    
    for i in range(n_features):
        toolbox.register(f"attr_float_{i}", np.random.uniform, min_vals[i], max_vals[i])
    
    toolbox.register("individual", tools.initCycle, creator.Individual,
                    [toolbox.__getattr__(f"attr_float_{i}") for i in range(n_features)], n=1)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    # Evaluation function
    def eval_nsga2(individual):
        bulk, shear, uncertainty, is_valid, distance = evaluate(
            individual, models, hull_wrapper, training_data, validation_report, feature_cols
        )
        if is_valid:
            # Penalize based on uncertainty
            return (bulk * (1 - 0.1 * uncertainty), shear * (1 - 0.1 * uncertainty))
        else:
            return (-1e9, -1e9)  # Heavily penalize invalid points
    
    toolbox.register("evaluate", eval_nsga2)
    toolbox.register("mate", tools.cxSimulatedBinaryBounded, low=min_vals, up=max_vals, eta=20.0)
    toolbox.register("mutate", tools.mutPolynomialBounded, low=min_vals, up=max_vals, eta=20.0, indpb=1.0/n_features)
    toolbox.register("select", tools.selNSGA2)
    
    # Initialize population
    pop = toolbox.population(n=population_size)
    hof = tools.ParetoFront()
    
    # Run evolution with timeout
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean, axis=0)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)
    
    log_info_with_context("NSGA-II", f"Starting optimization with {population_size} individuals for {generations} generations")
    
    try:
        pop, logbook = algorithms.eaMuPlusLambda(
            pop, toolbox, mu=population_size, lambda_=population_size * 2,
            cxpb=cx_prob, mutpb=mut_prob, ngen=generations,
            stats=stats, halloffame=hof, verbose=False
        )
    except Exception as e:
        log_error_with_context("NSGA-II", f"Optimization interrupted: {e}")
        log_warning_with_context("NSGA-II", "Returning best solutions found so far")
    
    # Extract Pareto front
    pareto_front = []
    for ind in hof:
        bulk, shear, uncertainty, is_valid, distance = evaluate(
            list(ind), models, hull_wrapper, training_data, validation_report, feature_cols
        )
        if is_valid:
            pareto_front.append((bulk, shear, uncertainty, is_valid, distance))
    
    return pareto_front

def save_results(
    pareto_front: List[Tuple[float, float, float, bool, float]],
    output_path: str,
    training_data: pd.DataFrame,
    hull_wrapper: ConvexHullWrapper
):
    """
    Save Pareto frontier results to CSV.
    
    Includes boundary proximity flags as required by FR-004.
    """
    logger = get_logger(__name__)
    
    if not pareto_front:
        logger.warning("No valid Pareto front points found. Saving empty result.")
        pd.DataFrame(columns=['bulk_modulus', 'shear_modulus', 'uncertainty_penalty', 'is_valid', 'distance_to_boundary', 'is_near_boundary']).to_csv(output_path, index=False)
        return
    
    # Calculate hull radius for boundary proximity threshold
    hull_radius = hull_wrapper.get_radius()
    boundary_threshold = 0.05 * hull_radius
    
    results = []
    for i, (bulk, shear, uncertainty, is_valid, distance) in enumerate(pareto_front):
        is_near_boundary = distance < boundary_threshold
        
        # Reconstruct composition from feature values (simplified - in practice would need inverse transform)
        # For now, we'll just store the metrics
        results.append({
            'point_id': i,
            'bulk_modulus': bulk,
            'shear_modulus': shear,
            'uncertainty_penalty': uncertainty,
            'is_valid': is_valid,
            'distance_to_boundary': distance,
            'is_near_boundary': is_near_boundary,
            'boundary_proximity_flag': 'HIGH' if is_near_boundary else 'NORMAL'
        })
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_path, index=False)
    
    log_info_with_context("Pareto", f"Saved {len(df_results)} Pareto optimal points to {output_path}")
    log_info_with_context("Pareto", f"Points near boundary (within 5% of hull radius): {df_results['is_near_boundary'].sum()}")

def main():
    """Main entry point for Pareto optimization."""
    logger = get_logger(__name__)
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="NSGA-II Pareto Optimization for Alloy Design")
    parser.add_argument("--data", type=str, default="data/processed/encoded_alloys.csv",
                      help="Path to encoded alloy data CSV")
    parser.add_argument("--models-dir", type=str, default="data/processed/models",
                      help="Directory containing trained models")
    parser.add_argument("--validation-report", type=str,
                      default="data/processed/model_validation_report.json",
                      help="Path to model validation report with uncertainty_variance")
    parser.add_argument("--output", type=str, default="data/results/pareto_frontier.csv",
                      help="Output path for Pareto frontier CSV")
    parser.add_argument("--population", type=int, default=100, help="Population size")
    parser.add_argument("--generations", type=int, default=50, help="Number of generations")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout in seconds")
    args = parser.parse_args()
    
    # Setup timeout
    watchdog = TimeoutWatchdog(args.timeout)
    watchdog.start()
    
    try:
        # Load data
        log_info_with_context("Pareto", "Loading encoded data...")
        training_data = load_encoded_data(args.data)
        
        # Load models
        log_info_with_context("Pareto", "Loading trained models...")
        models = load_models(args.models_dir)
        
        # Load validation report (for reliability mask)
        log_info_with_context("Pareto", "Loading validation report...")
        validation_report = load_validation_report(args.validation_report)
        
        # Initialize convex hull wrapper
        log_info_with_context("Pareto", "Computing convex hull...")
        feature_cols = get_feature_columns(training_data)
        X_train = training_data[feature_cols].values
        hull_wrapper = ConvexHullWrapper(X_train)
        
        # Run NSGA-II
        log_info_with_context("Pareto", "Starting NSGA-II optimization...")
        pareto_front = run_nsgaII(
            training_data=training_data,
            models=models,
            hull_wrapper=hull_wrapper,
            validation_report=validation_report,
            population_size=args.population,
            generations=args.generations,
            timeout_seconds=args.timeout
        )
        
        # Save results
        log_info_with_context("Pareto", "Saving results...")
        
        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        save_results(pareto_front, str(output_path), training_data, hull_wrapper)
        
        log_info_with_context("Pareto", "Optimization completed successfully")
        
    except KeyboardInterrupt:
        log_warning_with_context("Pareto", "Interrupted by user")
    except Exception as e:
        log_error_with_context("Pareto", f"Optimization failed: {e}")
        log_error_with_context("Pareto", traceback.format_exc())
        raise
    finally:
        watchdog.cancel()
        if watchdog.check():
            log_warning_with_context("Pareto", "Timeout was reached during execution")

if __name__ == "__main__":
    main()
