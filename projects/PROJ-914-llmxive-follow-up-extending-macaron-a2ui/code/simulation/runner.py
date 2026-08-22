"""
Simulation runner for the llmXive A2UI latency study.

Implements the core simulation loop with:
- Latency injection
- User patience modeling (exponential decay)
- Deterministic fallback generation
- Density iteration {1, 3, 5, 10}
- Borderline confidence handling (score == threshold -> Ambiguous)
"""

import os
import sys
import time
import json
import argparse
import logging
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Local imports matching API surface
from config import RANDOM_SEED
from simulation.patience import sample_patience
from simulation.rubric import calculate_alignment_score, calculate_latency_penalty
from models.fallback import FallbackGenerator
from models.router import MockRouter
from data.models import InteractionTurn, RoutingDecision, SimulationRun
from utils.logging import get_experiment_logger, log_metric, log_experiment_start, log_experiment_end

# Set seeds for reproducibility
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Explicit density levels for deterministic fallback (FR-004, Constitution Principle VII)
DENSITY_LEVELS = [1, 3, 5, 10]

# Router confidence threshold
ROUTER_THRESHOLD = 0.75

class MockGenerativeModel:
    """Mock generative model for simulation (replaces heavy model inference)."""

    def __init__(self, seed: int = RANDOM_SEED):
        self.seed = seed
        random.seed(seed)

    def generate_ui(self, query: str, complexity: float, density: int) -> Dict[str, Any]:
        """
        Generate a mock UI response.

        In a real run, this would invoke the quantized DistilGPT2 model.
        Here we simulate the *structure* and *latency* of generation.
        """
        # Simulate generation time based on complexity and density
        # Base time + complexity factor + density factor
        base_time = 0.2  # 200ms base
        gen_time = base_time + (complexity * 0.1) + (density * 0.05)

        # Simulate UI elements count (proportional to density)
        # Real model would generate actual UI components
        element_count = density * random.randint(2, 5)

        return {
            "ui_elements": element_count,
            "generation_time_ms": int(gen_time * 1000),
            "response_text": f"Generated UI for: {query[:20]}... (density={density})",
            "density_used": density
        }

def load_annotated_data(path: str) -> pd.DataFrame:
    """
    Load the annotated dataset from CSV.

    Args:
        path: Path to the annotated CSV file

    Returns:
        DataFrame with annotated interaction turns
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Annotated data file not found: {path}")

    df = pd.read_csv(path)

    # Validate required columns
    required_cols = ['query', 'ground_truth_intent', 'complexity_score', 'label']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in annotated data: {missing}")

    return df

def simulate_interaction(
    row: Dict[str, Any],
    router: MockRouter,
    fallback: FallbackGenerator,
    generative_model: MockGenerativeModel,
    latency_config: Dict[str, float],
    density: int
) -> SimulationRun:
    """
    Simulate a single interaction turn.

    Args:
        row: Interaction turn data
        router: Intent classifier router
        fallback: Deterministic fallback generator
        generative_model: Generative UI model
        latency_config: Latency injection parameters
        density: Information density level

    Returns:
        SimulationRun object with results
    """
    query = row['query']
    complexity = float(row.get('complexity_score', 1.0))
    ground_truth = row.get('ground_truth_intent', 'unknown')

    # 1. Route the query
    router_result = router.route(query)
    confidence = router_result['confidence']
    intent = router_result['predicted_intent']

    # Handle borderline confidence scores (if score == threshold, route to Ambiguous)
    # This ensures deterministic behavior at the boundary
    if abs(confidence - ROUTER_THRESHOLD) < 1e-9:
        intent = 'ambiguous'
        confidence = ROUTER_THRESHOLD - 0.01  # Slightly below threshold

    # 2. Calculate injected latency
    # Latency is drawn from the config distribution
    if router_result['is_high_confidence']:
        # High confidence: lower latency (direct path)
        latency_ms = random.gauss(latency_config['mean_high'], latency_config['std_high'])
    else:
        # Ambiguous: higher latency (fallback path)
        latency_ms = random.gauss(latency_config['mean_ambiguous'], latency_config['std_ambiguous'])

    latency_ms = max(0, latency_ms)  # No negative latency

    # 3. Sample user patience
    patience_seconds = sample_patience()
    patience_ms = patience_seconds * 1000

    # 4. Determine if user abandons
    total_time_ms = latency_ms  # Add generation time later
    abandoned = total_time_ms > patience_ms

    # 5. Generate response
    if abandoned:
        # User abandoned before response
        ui_result = {
            "ui_elements": 0,
            "generation_time_ms": 0,
            "response_text": "ABANDONED",
            "density_used": density
        }
        event_type = "abandonment"
    elif not router_result['is_high_confidence']:
        # Ambiguous: use fallback
        fallback_result = fallback.generate_fallback(query)
        ui_result = {
            "ui_elements": fallback_result.get('element_count', 1),
            "generation_time_ms": int(random.uniform(50, 150)),
            "response_text": fallback_result.get('text', ''),
            "density_used": density
        }
        event_type = "fallback" if fallback_result.get('matched', False) else "no_match"
    else:
        # High confidence: use generative model
        gen_result = generative_model.generate_ui(query, complexity, density)
        ui_result = {
            "ui_elements": gen_result['ui_elements'],
            "generation_time_ms": gen_result['generation_time_ms'],
            "response_text": gen_result['response_text'],
            "density_used": density
        }
        event_type = "generative"

    # 6. Calculate total time
    generation_time_ms = ui_result['generation_time_ms']
    total_time_ms = latency_ms + generation_time_ms

    # Check abandonment again with full time
    if total_time_ms > patience_ms and not abandoned:
        abandoned = True
        event_type = "abandonment"
        ui_result['ui_elements'] = 0
        ui_result['generation_time_ms'] = 0
        ui_result['response_text'] = "ABANDONED"

    # 7. Calculate alignment score
    # Using the rubric: score = 0.4 * intent_match + 0.3 * (1 - latency_penalty) + 0.3 * ui_completeness
    intent_match = 1.0 if intent == ground_truth else 0.0
    latency_penalty = calculate_latency_penalty(total_time_ms / 1000.0)  # Convert to seconds
    ui_completeness = ui_result['ui_elements'] / max(1, density * 5)  # Normalize by expected max
    ui_completeness = min(1.0, ui_completeness)

    alignment_score = calculate_alignment_score(
        intent_match=intent_match,
        latency_penalty=latency_penalty,
        ui_completeness=ui_completeness
    )

    # 8. Build result
    run = SimulationRun(
        query=query,
        ground_truth_intent=ground_truth,
        predicted_intent=intent,
        router_confidence=confidence,
        router_decision='ambiguous' if not router_result['is_high_confidence'] else 'high_confidence',
        latency_ms=int(latency_ms),
        generation_time_ms=ui_result['generation_time_ms'],
        total_time_ms=int(total_time_ms),
        patience_ms=int(patience_ms),
        abandoned=abandoned,
        event_type=event_type,
        ui_element_count=ui_result['ui_elements'],
        density_level=density,
        alignment_score=round(alignment_score, 4),
        intent_match=intent_match,
        latency_penalty=round(latency_penalty, 4),
        ui_completeness=round(ui_completeness, 4),
        timestamp=time.time()
    )

    return run

def run_simulation(
    data_path: str,
    latency_config: Dict[str, float],
    density_levels: List[int] = DENSITY_LEVELS,
    seed: int = RANDOM_SEED
) -> List[SimulationRun]:
    """
    Run the full simulation over the dataset.

    Iterates through explicit density levels {1, 3, 5, 10} for deterministic fallback.

    Args:
        data_path: Path to annotated CSV
        latency_config: Latency injection parameters
        density_levels: List of density levels to test
        seed: Random seed

    Returns:
        List of SimulationRun objects
    """
    random.seed(seed)
    np.random.seed(seed)

    # Load data
    logger = get_experiment_logger("simulation")
    logger.info(f"Loading annotated data from: {data_path}")
    df = load_annotated_data(data_path)
    logger.info(f"Loaded {len(df)} interaction turns")

    # Initialize components
    router = MockRouter()
    fallback = FallbackGenerator()
    generative_model = MockGenerativeModel(seed=seed)

    results = []

    # Iterate through each density level (FR-004, Constitution Principle VII)
    for density in density_levels:
        logger.info(f"Starting simulation for density level: {density}")

        for idx, row in df.iterrows():
            run = simulate_interaction(
                row=row.to_dict(),
                router=router,
                fallback=fallback,
                generative_model=generative_model,
                latency_config=latency_config,
                density=density
            )
            results.append(run)

            # Log progress
            if (idx + 1) % 100 == 0:
                logger.info(f"Processed {idx + 1}/{len(df)} rows at density {density}")

    logger.info(f"Simulation complete: {len(results)} runs across {len(density_levels)} density levels")
    return results

def save_simulation_results(results: List[SimulationRun], output_path: str):
    """
    Save simulation results to CSV.

    Args:
        results: List of SimulationRun objects
        output_path: Output file path
    """
    if not results:
        raise ValueError("No results to save")

    # Convert to DataFrame
    data = []
    for r in results:
        data.append({
            'query': r.query,
            'ground_truth_intent': r.ground_truth_intent,
            'predicted_intent': r.predicted_intent,
            'router_confidence': r.router_confidence,
            'router_decision': r.router_decision,
            'latency_ms': r.latency_ms,
            'generation_time_ms': r.generation_time_ms,
            'total_time_ms': r.total_time_ms,
            'patience_ms': r.patience_ms,
            'abandoned': r.abandoned,
            'event_type': r.event_type,
            'ui_element_count': r.ui_element_count,
            'density_level': r.density_level,
            'alignment_score': r.alignment_score,
            'intent_match': r.intent_match,
            'latency_penalty': r.latency_penalty,
            'ui_completeness': r.ui_completeness,
            'timestamp': r.timestamp
        })

    df = pd.DataFrame(data)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logging.info(f"Saved {len(df)} results to {output_path}")

def main():
    """Main entry point for simulation runner."""
    parser = argparse.ArgumentParser(description="Run A2UI latency simulation")
    parser.add_argument("--input", type=str, required=True, help="Path to annotated CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV")
    parser.add_argument("--density", type=str, default="1,3,5,10", help="Comma-separated density levels")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    logger = get_experiment_logger("simulation")
    log_experiment_start(logger, "T024b-density-iteration")

    # Parse density levels
    density_levels = [int(x.strip()) for x in args.density.split(",")]
    logger.info(f"Running simulation with density levels: {density_levels}")

    # Latency configuration (realistic values for CPU inference)
    latency_config = {
        "mean_high": 0.15,      # 150ms for high confidence
        "std_high": 0.05,       # 50ms std
        "mean_ambiguous": 0.35, # 350ms for ambiguous (fallback)
        "std_ambiguous": 0.1    # 100ms std
    }

    # Run simulation
    try:
        results = run_simulation(
            data_path=args.input,
            latency_config=latency_config,
            density_levels=density_levels,
            seed=args.seed
        )

        # Save results
        save_simulation_results(results, args.output)

        log_experiment_end(logger, "success", {
            "total_runs": len(results),
            "density_levels": density_levels,
            "output_file": args.output
        })

    except Exception as e:
        log_error(logger, str(e))
        raise

if __name__ == "__main__":
    main()