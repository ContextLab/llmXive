"""
Task T022: Integrate code/utils/physics_sim.py to simulate reconstructed states in PyBullet.

This script loads 3D reconstructed states from data/processed/reconstructed_states.json,
initializes a PyBullet simulation using the PhysicsSimWrapper, runs the simulation,
and records the simulation results (success/failure, final states) to data/processed/simulation_results.json.

It strictly uses real data and fails loudly if the input file is missing or corrupted.
"""
import os
import sys
import json
import logging
import time
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.physics_sim import SimulationConfig, SimulationResult, PhysicsSimWrapper, run_physics_validation
from utils.logging_config import get_logger, fail_loudly
from utils.error_handler import PhysicsSimError

# Configure logging
logger = get_logger(__name__)

INPUT_FILE = os.path.join(project_root, "data", "processed", "reconstructed_states.json")
OUTPUT_FILE = os.path.join(project_root, "data", "processed", "simulation_results.json")
LOG_FILE = os.path.join(project_root, "data", "processed", "simulation_errors.log")

def load_reconstructed_states(filepath: str) -> list:
    """
    Loads reconstructed 3D states from a JSON file.
    Fails loudly if the file does not exist or is invalid.
    """
    if not os.path.exists(filepath):
        fail_loudly(
            logger,
            f"Input file not found: {filepath}. "
            "Ensure T021 (3D reconstruction) has completed successfully."
        )

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        if not isinstance(data, list):
            fail_loudly(
                logger,
                f"Invalid data format in {filepath}. Expected a list of state records."
            )
        logger.info(f"Loaded {len(data)} reconstructed state records from {filepath}")
        return data
    except json.JSONDecodeError as e:
        fail_loudly(logger, f"Failed to parse JSON in {filepath}: {e}")
    except Exception as e:
        fail_loudly(logger, f"Unexpected error loading {filepath}: {e}")

def run_simulation_batch(states: list, config: SimulationConfig) -> list:
    """
    Runs physics simulation for a batch of reconstructed states.
    Returns a list of SimulationResult objects.
    """
    results = []
    wrapper = PhysicsSimWrapper(config)

    try:
        wrapper.initialize()
        logger.info("Physics simulation environment initialized.")
    except Exception as e:
        fail_loudly(logger, f"Failed to initialize PyBullet simulation: {e}")

    for idx, state_record in enumerate(states):
        try:
            # Extract state data from the record
            # Expected keys based on T021/EstimatedState3D: positions, velocities, orientations, confidence_score
            positions = np.array(state_record.get("positions", []))
            velocities = np.array(state_record.get("velocities", []))
            orientations = np.array(state_record.get("orientations", []))
            confidence = state_record.get("confidence_score", 1.0)

            if positions.size == 0:
                logger.warning(f"Skipping sample {idx}: Empty positions.")
                results.append(SimulationResult(
                    sample_id=state_record.get("id", f"unknown_{idx}"),
                    success=False,
                    error="Empty positions",
                    final_state=None,
                    duration=0.0
                ))
                continue

            # Run validation/simulation
            # The wrapper expects specific formats; we adapt the input to the wrapper's API
            sim_result = run_physics_validation(
                wrapper,
                positions=positions,
                velocities=velocities,
                orientations=orientations,
                config=config
            )

            results.append(sim_result)

            if idx % 10 == 0:
                logger.info(f"Processed {idx}/{len(states)} samples.")

        except PhysicsSimError as e:
            logger.error(f"Simulation failed for sample {idx}: {e}")
            results.append(SimulationResult(
                sample_id=state_record.get("id", f"unknown_{idx}"),
                success=False,
                error=str(e),
                final_state=None,
                duration=0.0
            ))
        except Exception as e:
            logger.error(f"Unexpected error processing sample {idx}: {e}")
            results.append(SimulationResult(
                sample_id=state_record.get("id", f"unknown_{idx}"),
                success=False,
                error=f"Unexpected error: {str(e)}",
                final_state=None,
                duration=0.0
            ))
        finally:
            # Optional: cleanup per sample if needed, but wrapper manages global state
            pass

    wrapper.cleanup()
    logger.info("Physics simulation batch completed.")
    return results

def save_results(results: list, filepath: str):
    """
    Saves simulation results to a JSON file.
    Converts SimulationResult dataclasses to dictionaries.
    """
    output_data = []
    for res in results:
        res_dict = {
            "sample_id": res.sample_id,
            "success": res.success,
            "error": res.error,
            "duration": res.duration,
            "final_state": res.final_state.tolist() if res.final_state is not None else None
        }
        output_data.append(res_dict)

    try:
        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Saved {len(results)} simulation results to {filepath}")
    except Exception as e:
        fail_loudly(logger, f"Failed to write results to {filepath}: {e}")

def main():
    """
    Main entry point for T022.
    """
    logger.info("Starting T022: Physics Simulation Integration")

    # Configuration for the simulation
    # Adjust these parameters based on the specific physics constraints required
    sim_config = SimulationConfig(
        gravity=[0.0, 0.0, -9.81],
        time_step=0.01,
        simulation_duration=2.0,  # seconds
        enable_collision=True,
        enable_friction=True
    )

    # Load data
    states = load_reconstructed_states(INPUT_FILE)
    if not states:
        fail_loudly(logger, "No states to simulate. Input file is empty.")

    # Run simulation
    logger.info(f"Starting simulation for {len(states)} samples...")
    start_time = time.time()
    results = run_simulation_batch(states, sim_config)
    end_time = time.time()

    logger.info(f"Total simulation time: {end_time - start_time:.2f} seconds")

    # Save results
    save_results(results, OUTPUT_FILE)

    # Summary stats
    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count
    logger.info(f"Simulation Summary: {success_count} passed, {fail_count} failed.")

    return 0

if __name__ == "__main__":
    sys.exit(main())