import os
import sys
import json
import logging
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# Import from project utilities
from utils.physics_sim import SimulationConfig, SimulationResult, PhysicsSimWrapper, run_physics_validation
from utils.logging_config import get_logger, log_simulation_error
from utils.error_handler import handle_simulation_failure, PhysicsSimError

logger = get_logger(__name__)

@dataclass
class LabelAssignmentConfig:
    """Configuration for the label assignment logic."""
    gravity_threshold: float = 9.81  # m/s^2, tolerance for gravity check
    collision_threshold: float = 0.01  # meters, tolerance for collision
    energy_threshold: float = 1.0  # Joules, tolerance for energy conservation
    perturbation_subset_ratio: float = 0.1  # 10% of samples for synthetic perturbation
    perturbation_magnitude: float = 2.0  # m/s upward velocity for perturbation
    random_seed: int = 42
    output_dir: str = "data/processed"

@dataclass
class LabelAssignmentResult:
    """Result of the label assignment process for a single clip."""
    clip_id: str
    physical_label: str  # "valid", "invalid", or "null"
    reason: str
    confidence_score: float
    perturbation_type: int  # 0 for natural, 1 for synthetic
    violation_details: Optional[Dict[str, Any]] = None

def load_simulation_results(input_path: str) -> List[Dict[str, Any]]:
    """Load reconstructed states and simulation results from JSON."""
    if not os.path.exists(input_path):
        logger.error(f"Simulation results file not found: {input_path}")
        raise FileNotFoundError(f"Simulation results file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Ensure we have a list of results
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Invalid simulation results format. Expected a list or dict with 'results' key.")

def check_gravity_consistency(state: Dict[str, Any], threshold: float) -> Tuple[bool, str]:
    """
    Check if the object's vertical acceleration is consistent with gravity.
    Returns (is_valid, reason_string).
    """
    # Extract velocities at different time steps to estimate acceleration
    # Assuming state contains a list of positions/velocities over time
    if 'velocities' not in state or 'positions' not in state:
        return False, "Missing velocity or position data for gravity check"
    
    velocities = state['velocities']
    if len(velocities) < 2:
        return True, "Insufficient data points for acceleration calculation"
    
    # Calculate vertical acceleration (z-axis)
    # Simple finite difference: a = (v2 - v1) / dt
    # Assuming uniform time steps, we can just look at velocity differences
    z_velocities = [v[2] if len(v) >= 3 else 0.0 for v in velocities]
    
    # Check for gravity defiance (e.g., constant upward acceleration)
    # In a valid physics simulation, vertical velocity should decrease due to gravity
    # We check if the change in velocity is consistent with -9.81 m/s^2
    avg_z_accel = 0.0
    if len(z_velocities) > 1:
        # Approximate acceleration as the average change in velocity
        # This is a simplified check; a real implementation would use timestamps
        z_changes = [z_velocities[i+1] - z_velocities[i] for i in range(len(z_velocities)-1)]
        avg_z_accel = sum(z_changes) / len(z_changes)
    
    # If acceleration is significantly positive (upward), it's a violation
    # Gravity should pull down (negative acceleration)
    if avg_z_accel > 0.5:  # Tolerance for noise
        return False, f"Gravity defiance detected: upward acceleration {avg_z_accel:.2f} m/s^2"
    
    return True, "Gravity check passed"

def check_collision_constraints(state: Dict[str, Any], threshold: float) -> Tuple[bool, str]:
    """
    Check for collision violations (e.g., objects passing through each other).
    Returns (is_valid, reason_string).
    """
    # This is a simplified check. In a real implementation, we would use the physics engine
    # to detect collisions during the simulation.
    # For now, we check if any object's position is below a ground plane (y=0)
    # or if objects overlap significantly.
    
    if 'positions' not in state:
        return True, "No position data for collision check"
    
    positions = state['positions']
    for pos in positions:
        # Assuming y-axis is up, check if object is below ground
        if len(pos) >= 2 and pos[1] < -threshold:
            return False, f"Collision with ground detected: object at y={pos[1]:.2f}"
    
    return True, "Collision check passed"

def check_energy_conservation(state: Dict[str, Any], threshold: float) -> Tuple[bool, str]:
    """
    Check for energy conservation violations (e.g., gaining energy without external force).
    Returns (is_valid, reason_string).
    """
    # Simplified check: total kinetic energy should not increase dramatically without cause
    if 'velocities' not in state or 'mass' not in state:
        return True, "Insufficient data for energy check"
    
    velocities = state['velocities']
    mass = state['mass']
    
    if len(velocities) < 2:
        return True, "Insufficient data points for energy change calculation"
    
    # Calculate kinetic energy at first and last time steps
    # KE = 0.5 * m * v^2
    v_first = np.linalg.norm(velocities[0])
    v_last = np.linalg.norm(velocities[-1])
    
    ke_first = 0.5 * mass * (v_first ** 2)
    ke_last = 0.5 * mass * (v_last ** 2)
    
    # Check for significant energy gain (more than threshold)
    if ke_last > ke_first * (1 + threshold):
        return False, f"Energy violation: KE increased from {ke_first:.2f} to {ke_last:.2f} J"
    
    return True, "Energy check passed"

def apply_synthetic_perturbation(state: Dict[str, Any], config: LabelAssignmentConfig) -> Dict[str, Any]:
    """
    Apply a known synthetic perturbation to the state.
    For this task, we add a constant upward velocity to the object.
    """
    perturbed_state = state.copy()
    
    if 'velocities' not in perturbed_state:
        logger.warning("No velocities in state to perturb")
        return perturbed_state
    
    # Add upward velocity (z-axis) to all velocity vectors
    perturbation_vector = [0.0, 0.0, config.perturbation_magnitude]
    
    new_velocities = []
    for v in perturbed_state['velocities']:
        new_v = list(v)
        if len(new_v) >= 3:
            new_v[2] += config.perturbation_magnitude
        else:
            new_v.extend([0.0] * (3 - len(new_v)))
            new_v[2] += config.perturbation_magnitude
        new_velocities.append(new_v)
    
    perturbed_state['velocities'] = new_velocities
    perturbed_state['perturbation_applied'] = True
    
    logger.info(f"Applied synthetic perturbation: upward velocity +{config.perturbation_magnitude} m/s")
    return perturbed_state

def assign_label(
    state: Dict[str, Any],
    clip_id: str,
    config: LabelAssignmentConfig,
    perturbation_type: int = 0
) -> LabelAssignmentResult:
    """
    Assign a physical label based on physics constraints.
    
    Args:
        state: Reconstructed 3D state dictionary
        clip_id: Unique identifier for the video clip
        config: LabelAssignmentConfig instance
        perturbation_type: 0 for natural, 1 for synthetic perturbation
    
    Returns:
        LabelAssignmentResult with label, reason, and metadata
    """
    violation_reasons = []
    is_valid = True
    
    # Run physics checks
    gravity_valid, gravity_reason = check_gravity_consistency(state, config.gravity_threshold)
    if not gravity_valid:
        is_valid = False
        violation_reasons.append(gravity_reason)
    
    collision_valid, collision_reason = check_collision_constraints(state, config.collision_threshold)
    if not collision_valid:
        is_valid = False
        violation_reasons.append(collision_reason)
    
    energy_valid, energy_reason = check_energy_conservation(state, config.energy_threshold)
    if not energy_valid:
        is_valid = False
        violation_reasons.append(energy_reason)
    
    # Determine final label
    if is_valid:
        physical_label = "valid"
        reason = "All physics checks passed"
    else:
        physical_label = "invalid"
        reason = "; ".join(violation_reasons)
    
    # Confidence score (simplified: 1.0 if valid, 0.0 if invalid)
    # In a real implementation, this could be based on the magnitude of violations
    confidence_score = 1.0 if is_valid else 0.0
    
    return LabelAssignmentResult(
        clip_id=clip_id,
        physical_label=physical_label,
        reason=reason,
        confidence_score=confidence_score,
        perturbation_type=perturbation_type,
        violation_details={
            "gravity": gravity_valid,
            "collision": collision_valid,
            "energy": energy_valid,
            "violations": violation_reasons
        } if not is_valid else None
    )

def save_labels(results: List[LabelAssignmentResult], output_path: str):
    """Save label assignment results to a JSON file."""
    output_data = {
        "results": [
            {
                "clip_id": r.clip_id,
                "physical_label": r.physical_label,
                "reason": r.reason,
                "confidence_score": r.confidence_score,
                "perturbation_type": r.perturbation_type,
                "violation_details": r.violation_details
            }
            for r in results
        ]
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved {len(results)} label assignments to {output_path}")

def main():
    """Main entry point for label assignment."""
    logger.info("Starting label assignment process")
    
    # Configuration
    config = LabelAssignmentConfig(
        output_dir="data/processed",
        perturbation_subset_ratio=0.1,
        perturbation_magnitude=2.0,
        random_seed=42
    )
    
    # Load simulation results
    simulation_input_path = "data/processed/simulation_results.json"
    try:
        simulation_results = load_simulation_results(simulation_input_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load simulation results: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(simulation_results)} simulation results")
    
    # Determine which samples to perturb (random subset)
    np.random.seed(config.random_seed)
    indices_to_perturb = set(
        np.random.choice(
            len(simulation_results),
            size=int(len(simulation_results) * config.perturbation_subset_ratio),
            replace=False
        )
    )
    
    logger.info(f"Selected {len(indices_to_perturb)} samples for synthetic perturbation")
    
    # Process each sample
    results = []
    for i, state in enumerate(simulation_results):
        clip_id = state.get('clip_id', f"clip_{i}")
        
        # Determine perturbation type
        perturbation_type = 1 if i in indices_to_perturb else 0
        
        # Apply perturbation if needed
        state_to_process = state
        if perturbation_type == 1:
            state_to_process = apply_synthetic_perturbation(state, config)
        
        # Assign label
        result = assign_label(
            state=state_to_process,
            clip_id=clip_id,
            config=config,
            perturbation_type=perturbation_type
        )
        
        results.append(result)
        
        # Log progress
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i+1}/{len(simulation_results)} samples")
    
    # Save results
    output_path = os.path.join(config.output_dir, "labels_temporary.json")
    save_labels(results, output_path)
    
    logger.info("Label assignment completed successfully")
    return results

if __name__ == "__main__":
    main()