"""
MD Simulation Runner using OpenMM.

Executes CPU-only Molecular Dynamics simulations with explicit solvent
and enforces a hard timeout for 1.5ns runs.
"""
import os
import sys
import signal
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
from openmm import app, Platform, Vec3
from openmm import unit
from openmm.app import PDBFile, ForceField, Modeller, State
from openmm import LangevinIntegrator, MonteCarloBarostat, CustomCVForce
from openmmtools import multistate

# Project imports
from utils.io import compute_sha256, write_json, ensure_directory, update_state, safe_copy
from utils.logger import get_logger, enforce_timeout, MDRunLogger

# Constants
SIMULATION_TIMEOUT_SECONDS = 450  # 7.5 minutes hard limit for 1.5ns run on CI
DEFAULT_STEPS_PER_FRAME = 500
DEFAULT_FRAME_COUNT = 1000  # Total frames to write
TOTAL_STEPS = DEFAULT_STEPS_PER_FRAME * DEFAULT_FRAME_COUNT

# Simulation parameters
TEMPERATURE = 300 * unit.kelvin
PRESSURE = 1 * unit.atmosphere
TIME_STEP = 2.0 * unit.femtoseconds
CONSERVATION_PARAM = 1.0 * unit.picosecond
NONBONDED_METHOD = app.PME
NONBONDED_CUTOFF = 1.0 * unit.nanometer

logger = get_logger(__name__)


class SimulationTimeoutError(Exception):
    """Raised when a simulation exceeds the allowed runtime."""
    pass


def setup_signal_timeout(timeout_seconds: int = SIMULATION_TIMEOUT_SECONDS):
    """
    Sets up a signal handler to kill the process if it exceeds the timeout.
    Only works on Unix-like systems.
    """
    def timeout_handler(signum, frame):
        raise SimulationTimeoutError(
            f"Simulation exceeded timeout of {timeout_seconds}s"
        )
    
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
    else:
        logger.warning("SIGALRM not available on this platform. Using thread-based timeout fallback.")
        # Fallback for Windows or platforms without SIGALRM
        def watchdog():
            time.sleep(timeout_seconds)
            os._exit(1)
        
        thread = threading.Thread(target=watchdog, daemon=True)
        thread.start()


def run_simulation(
    pdb_path: str,
    force_field_name: str,
    duration_ns: float,
    output_dir: str,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run a single MD simulation for a given complex and parameter set.
    
    Args:
        pdb_path: Path to the input PDB file (processed by setup.py).
        force_field_name: Name of the force field (e.g., 'ff14SB', 'CHARMM36m').
        duration_ns: Target simulation duration in nanoseconds.
        output_dir: Directory to save trajectory and state files.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing simulation metadata and output paths.
    """
    # Ensure output directory exists
    ensure_directory(output_dir)
    output_path = Path(output_dir) / f"simulation_{os.path.basename(pdb_path).replace('.pdb', '')}.nc"
    state_path = Path(output_dir) / f"simulation_{os.path.basename(pdb_path).replace('.pdb', '')}.json"
    
    logger.info(f"Starting simulation: {pdb_path} | FF: {force_field_name} | Duration: {duration_ns}ns")
    
    try:
        # Setup signal timeout
        # Calculate steps based on duration
        # duration_ns * 1e9 ns/s / (time_step in s) = steps
        # 1.5ns * 1e9 / (2e-15) = 750,000 steps
        # For 1.5ns target:
        target_steps = int(duration_ns * 1e9 / (TIME_STEP.value_in(unit.nanometers) * 1e-6))
        # Adjust for time_step unit conversion
        # Time step is 2.0 fs = 2.0e-15 s
        # Steps = duration_s / time_step_s
        steps_per_ns = 1e9 / (2.0e-15) # 500,000 steps per ns
        total_steps = int(duration_ns * steps_per_ns)
        
        # Cap steps for CI constraints if duration is too long
        # 1.5ns is the max target, so 750,000 steps is fine.
        # But we also have a hard time limit.
        
        logger.info(f"Running {total_steps} steps for {duration_ns}ns simulation.")
        
        # Load PDB
        pdb_file = PDBFile(pdb_path)
        
        # Select Force Field
        # Map common names to OpenMM available force fields
        ff_mapping = {
            'ff14SB': 'amber14-all.xml', # Assuming amber14 is available or mapped
            'CHARMM36m': 'charmm36.xml',
            'ffSB': 'amber99sb.xml'
        }
        
        ff_filename = ff_mapping.get(force_field_name, 'amber14-all.xml')
        
        # Try to load force field, fallback to standard if specific not found
        try:
            force_field = ForceField(ff_filename)
        except Exception as e:
            logger.warning(f"Force field {ff_filename} not found, trying 'amber14-all.xml': {e}")
            force_field = ForceField('amber14-all.xml')
        
        # Create System
        system = force_field.createSystem(
            pdb_file.topology,
            nonbondedMethod=NONBONDED_METHOD,
            nonbondedCutoff=NONBONDED_CUTOFF,
            constraints=app.HBonds,
            rigidWater=True
        )
        
        # Add Barostat
        system.addForce(MonteCarloBarostat(PRESSURE, TEMPERATURE, 25))
        
        # Integrator
        integrator = LangevinIntegrator(
            TEMPERATURE,
            1.0 / unit.picosecond,
            TIME_STEP
        )
        integrator.setRandomNumberSeed(seed)
        
        # Platform
        # Force CPU usage
        platform = Platform.getPlatformByName('CPU')
        platform.setPropertyDefaultValue('CudaPrecision', 'mixed')
        
        # Simulation Object
        simulation = app.Simulation(
            pdb_file.topology,
            system,
            integrator,
            platform
        )
        
        simulation.context.setPositions(pdb_file.positions)
        
        # Minimize energy
        logger.info("Minimizing energy...")
        simulation.minimizeEnergy(maxIterations=1000)
        
        # Equilibrate (brief)
        logger.info("Equilibrating...")
        simulation.context.setVelocitiesToTemperature(TEMPERATURE)
        simulation.step(1000)
        
        # Production Run
        logger.info("Starting production run...")
        
        # Setup timeout
        setup_signal_timeout(SIMULATION_TIMEOUT_SECONDS)
        
        # Define reporter
        # Calculate steps per frame to match output file size constraints
        # If we want 1000 frames for 1.5ns, and total steps is 750,000
        # steps_per_frame = 750
        steps_per_frame = total_steps // DEFAULT_FRAME_COUNT
        if steps_per_frame < 1:
            steps_per_frame = 1
        
        simulation.reporters.append(app.NetCDFReporter(
            str(output_path),
            steps_per_frame,
            reportInterval=steps_per_frame
        ))
        
        simulation.reporters.append(app.StateDataReporter(
            sys.stdout,
            steps_per_frame,
            step=True,
            potentialEnergy=True,
            temperature=True,
            progress=True,
            remainingTime=True,
            speed=True,
            totalSteps=total_steps
        ))
        
        simulation.step(total_steps)
        
        # Clear timeout
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
        
        logger.info(f"Simulation completed successfully. Output: {output_path}")
        
        # Calculate checksum
        checksum = compute_sha256(str(output_path))
        
        # Save state metadata
        state_data = {
            "complex_id": Path(pdb_path).stem,
            "force_field": force_field_name,
            "duration_ns": duration_ns,
            "seed": seed,
            "total_steps": total_steps,
            "steps_per_frame": steps_per_frame,
            "output_file": str(output_path),
            "checksum": checksum,
            "status": "completed",
            "timestamp": time.time()
        }
        write_json(state_data, str(state_path))
        
        return state_data
        
    except SimulationTimeoutError as e:
        logger.error(f"Simulation timed out: {e}")
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
        
        # Save partial state if possible
        state_data = {
            "complex_id": Path(pdb_path).stem,
            "force_field": force_field_name,
            "duration_ns": duration_ns,
            "status": "timeout",
            "error": str(e),
            "timestamp": time.time()
        }
        write_json(state_data, str(state_path))
        raise e
        
    except Exception as e:
        logger.error(f"Simulation failed with unexpected error: {e}")
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
        
        state_data = {
            "complex_id": Path(pdb_path).stem,
            "force_field": force_field_name,
            "duration_ns": duration_ns,
            "status": "failed",
            "error": str(e),
            "timestamp": time.time()
        }
        write_json(state_data, str(state_path))
        raise e


def main():
    parser = argparse.ArgumentParser(description="Run MD simulation for a single complex.")
    parser.add_argument("--pdb", required=True, help="Path to input PDB file")
    parser.add_argument("--ff", default="ff14SB", help="Force field name")
    parser.add_argument("--duration", type=float, default=1.5, help="Simulation duration in ns")
    parser.add_argument("--output-dir", required=True, help="Output directory for trajectory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdb):
        logger.error(f"Input PDB file not found: {args.pdb}")
        sys.exit(1)
        
    try:
        run_simulation(
            pdb_path=args.pdb,
            force_field_name=args.ff,
            duration_ns=args.duration,
            output_dir=args.output_dir,
            seed=args.seed
        )
        logger.info("Simulation finished successfully.")
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()