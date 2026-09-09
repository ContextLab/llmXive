import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Import from existing API surface
from utils.physics_sim import SimulationResult, PhysicsSimWrapper
from utils.logging_config import get_logger
from utils.error_handler import handle_simulation_failure

logger = get_logger(__name__)

@dataclass
class LabelAssignmentConfig:
    """Configuration for label assignment logic."""
    confidence_threshold: float = 0.9
    physics_timeout: float = 30.0
    output_labels_path: str = "data/processed/labels.csv"
    output_metadata_path: str = "data/processed/metadata.json"
    output_log_path: str = "data/processed/excluded_samples.log"

@dataclass
class LabelAssignmentResult:
    """Result of label assignment for a single sample."""
    sample_id: str
    label: str  # 'valid', 'invalid', or 'null'
    reason: str
    confidence: float
    simulation_success: bool

def load_simulation_results(results_path: str) -> List[Dict[str, Any]]:
    """
    Load simulation results from a JSON file.
    Expected format: list of dicts with keys: sample_id, success, confidence, details
    """
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Simulation results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def check_gravity_consistency(sim_result: Dict[str, Any]) -> bool:
    """Check if the simulation result indicates gravity consistency."""
    # Placeholder logic - in real implementation, this would analyze physics data
    details = sim_result.get('details', {})
    return details.get('gravity_check', True)

def check_collision_constraints(sim_result: Dict[str, Any]) -> bool:
    """Check if the simulation result indicates valid collision constraints."""
    details = sim_result.get('details', {})
    return details.get('collision_valid', True)

def check_energy_conservation(sim_result: Dict[str, Any]) -> bool:
    """Check if the simulation result indicates energy conservation."""
    details = sim_result.get('details', {})
    return details.get('energy_valid', True)

def assign_label(
    sample_id: str,
    sim_result: Dict[str, Any],
    config: LabelAssignmentConfig
) -> LabelAssignmentResult:
    """
    Assign a label ('valid', 'invalid', or 'null') based on simulation results and confidence.
    
    Logic:
    1. If simulation failed (success=False), assign 'null' with reason.
    2. If confidence < threshold, assign 'null' with reason.
    3. Otherwise, determine 'valid' or 'invalid' based on physics checks.
    """
    success = sim_result.get('success', False)
    confidence = sim_result.get('confidence', 0.0)
    
    if not success:
        reason = sim_result.get('error', 'Simulation failed')
        logger.warning(f"Sample {sample_id}: Simulation failed. Assigning 'null'. Reason: {reason}")
        return LabelAssignmentResult(
            sample_id=sample_id,
            label='null',
            reason=f"Simulation failed: {reason}",
            confidence=confidence,
            simulation_success=False
        )
    
    if confidence < config.confidence_threshold:
        reason = f"Reconstruction confidence ({confidence:.2f}) below threshold ({config.confidence_threshold})"
        logger.warning(f"Sample {sample_id}: {reason}. Assigning 'null'.")
        return LabelAssignmentResult(
            sample_id=sample_id,
            label='null',
            reason=reason,
            confidence=confidence,
            simulation_success=True
        )
    
    # Determine validity based on physics checks
    gravity_ok = check_gravity_consistency(sim_result)
    collision_ok = check_collision_constraints(sim_result)
    energy_ok = check_energy_conservation(sim_result)
    
    if gravity_ok and collision_ok and energy_ok:
        label = 'valid'
        reason = "All physics constraints satisfied"
    else:
        issues = []
        if not gravity_ok: issues.append("gravity")
        if not collision_ok: issues.append("collision")
        if not energy_ok: issues.append("energy")
        label = 'invalid'
        reason = f"Physics violations detected: {', '.join(issues)}"
    
    logger.info(f"Sample {sample_id}: Assigned '{label}'. Reason: {reason}")
    return LabelAssignmentResult(
        sample_id=sample_id,
        label=label,
        reason=reason,
        confidence=confidence,
        simulation_success=True
    )

def save_labels(
    results: List[LabelAssignmentResult],
    config: LabelAssignmentConfig
) -> None:
    """
    Save labels to CSV and metadata to JSON.
    Also generates a log file for samples marked as 'null'.
    
    CRITICAL: All samples (including 'null') MUST be in labels.csv.
    The excluded_samples.log is for reference only.
    """
    # Ensure output directory exists
    labels_path = Path(config.output_labels_path)
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    
    metadata_path = Path(config.output_metadata_path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    log_path = Path(config.output_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write labels.csv
    # Format: sample_id,label,reason,confidence
    with open(labels_path, 'w') as f:
        f.write("sample_id,label,reason,confidence\n")
        for res in results:
            # Escape commas and quotes in reason
            safe_reason = res.reason.replace('"', '""')
            f.write(f'{res.sample_id},"{res.label}","{safe_reason}",{res.confidence:.4f}\n')
    
    # Write metadata.json
    metadata = {
        "total_samples": len(results),
        "valid_count": sum(1 for r in results if r.label == 'valid'),
        "invalid_count": sum(1 for r in results if r.label == 'invalid'),
        "null_count": sum(1 for r in results if r.label == 'null'),
        "threshold_used": config.confidence_threshold,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Write excluded_samples.log (only for 'null' labels)
    with open(log_path, 'w') as f:
        f.write(f"# Excluded/Null Samples Log\n")
        f.write(f"# Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Threshold: {config.confidence_threshold}\n\n")
        null_samples = [r for r in results if r.label == 'null']
        for res in null_samples:
            f.write(f"Sample ID: {res.sample_id}\n")
            f.write(f"  Label: {res.label}\n")
            f.write(f"  Reason: {res.reason}\n")
            f.write(f"  Confidence: {res.confidence:.4f}\n")
            f.write(f"  Simulation Success: {res.simulation_success}\n")
            f.write("-" * 40 + "\n")
        
        if not null_samples:
            f.write("No samples were marked as 'null'.\n")
    
    logger.info(f"Saved {len(results)} labels to {labels_path}")
    logger.info(f"Saved metadata to {metadata_path}")
    logger.info(f"Generated excluded samples log at {log_path} ({len(null_samples)} entries)")

def main():
    """
    Main entry point for label assignment.
    Expects simulation results to be available in a predefined location.
    """
    config = LabelAssignmentConfig()
    
    # Default path for simulation results (could be made configurable via env or args)
    sim_results_path = "data/processed/simulation_results.json"
    
    if not os.path.exists(sim_results_path):
        logger.error(f"Simulation results not found at {sim_results_path}")
        logger.error("Please run the physics simulation pipeline first.")
        sys.exit(1)
    
    try:
        sim_results = load_simulation_results(sim_results_path)
        logger.info(f"Loaded {len(sim_results)} simulation results")
    except Exception as e:
        logger.error(f"Failed to load simulation results: {e}")
        sys.exit(1)
    
    results = []
    for sim_result in sim_results:
        sample_id = sim_result.get('sample_id', 'unknown')
        try:
            res = assign_label(sample_id, sim_result, config)
            results.append(res)
        except Exception as e:
            logger.error(f"Error assigning label for {sample_id}: {e}")
            # Still assign a null label for failed assignments
            results.append(LabelAssignmentResult(
                sample_id=sample_id,
                label='null',
                reason=f"Assignment error: {str(e)}",
                confidence=0.0,
                simulation_success=False
            ))
    
    save_labels(results, config)
    logger.info("Label assignment completed successfully.")

if __name__ == "__main__":
    main()