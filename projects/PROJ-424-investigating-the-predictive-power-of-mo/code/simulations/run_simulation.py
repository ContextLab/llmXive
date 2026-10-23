"""
Real OpenMM simulation runner for calculating diffusion coefficients.
Produces a trajectory file (.xtc) and a log file.
"""
import logging
from pathlib import Path
from typing import Dict, Any

from openmm import app, unit, openmm
from openmm.app import XTCReporter, StateDataReporter

from config import Solvent, SimulationConfig, DEFAULT_SIMULATION_CONFIG
from .build_system import build_system

log = logging.getLogger(__name__)


def run_simulation(
    solvent: Solvent,
    config: SimulationConfig = DEFAULT_SIMULATION_CONFIG,
    duration_ns: float = 1.0,
    seed: int = 0,
) -> Dict[str, Any]:
    """
    Runs a real OpenMM simulation and writes a trajectory (.xtc) and a log file.

    Parameters
    ----------
    solvent : Solvent
        The solvent enum value.
    config : SimulationConfig
        Simulation configuration (force field, timestep, temperature, etc.).
    duration_ns : float
        Desired simulation length in nanoseconds.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    dict
        Dictionary with keys ``trajectory``, ``log`` and ``status``.
    """
    log.info(f"Running MD simulation for {solvent.value} ({duration_ns} ns, seed={seed})")

    # ------------------------------------------------------------------
    # 1. Build the OpenMM system, topology and initial positions
    # ------------------------------------------------------------------
    try:
        system, topology, positions = build_system(solvent, config, seed)
    except Exception as e:
        log.error(f"System building failed: {e}")
        raise RuntimeError(f"Failed to build system for {solvent.value}") from e

    # ------------------------------------------------------------------
    # 2. Set up the integrator (Langevin) with the configured temperature,
    #    friction coefficient and timestep. Seed the RNG for reproducibility.
    # ------------------------------------------------------------------
    integrator = openmm.LangevinMiddleIntegrator(
        config.temperature * unit.kelvin,
        1.0 / unit.picosecond,               # friction coefficient
        config.time_step * unit.femtoseconds, # timestep
    )
    integrator.setRandomNumberSeed(seed)

    # ------------------------------------------------------------------
    # 3. Create the Simulation object and initialise positions
    # ------------------------------------------------------------------
    simulation = app.Simulation(topology, system, integrator)
    simulation.context.setPositions(positions)

    # Energy minimisation
    simulation.minimizeEnergy()
    # Initialise velocities to the target temperature
    simulation.context.setVelocitiesToTemperature(config.temperature * unit.kelvin)

    # ------------------------------------------------------------------
    # 4. Prepare output directory and file paths
    # ------------------------------------------------------------------
    sim_dir = Path("data/raw/simulations")
    sim_dir.mkdir(parents=True, exist_ok=True)
    traj_path = sim_dir / f"{solvent.value}_{duration_ns}ns_seed{seed}.xtc"
    log_path = sim_dir / f"{solvent.value}_{duration_ns}ns_seed{seed}.log"

    # Write a simple header log file
    with open(log_path, "w") as f:
        f.write(f"Simulation for {solvent.value}\\n")
        f.write(f"Seed: {seed}\\n")
        f.write(f"Duration: {duration_ns} ns\\n")
        f.write(f"Time step: {config.time_step} fs\\n")

    # ------------------------------------------------------------------
    # 5. Attach reporters
    #    - XTCReporter writes the trajectory in GROMACS XTC format.
    #    - StateDataReporter appends a human‑readable line to the log file
    #      every ``report_interval`` steps.
    # ------------------------------------------------------------------
    report_interval = max(1, int(duration_ns * 1e6 / config.time_step // 1000))  # approx every 1000 steps
    simulation.reporters.append(
        XTCReporter(str(traj_path), report_interval)
    )
    simulation.reporters.append(
        StateDataReporter(
            str(log_path),
            report_interval,
            step=True,
            time=True,
            potentialEnergy=True,
            temperature=True,
        )
    )

    # ------------------------------------------------------------------
    # 6. Determine the number of integration steps needed for the requested duration.
    #    1 ns = 1e6 fs; steps = duration_ns * 1e6 / time_step
    # ------------------------------------------------------------------
    steps = int(duration_ns * 1e6 / config.time_step)
    if steps <= 0:
        raise ValueError("Computed number of steps is non‑positive. Check duration_ns and time_step.")

    log.info(f"Running production for {steps} steps (≈ {duration_ns} ns)")
    simulation.step(steps)

    return {
        "trajectory": str(traj_path),
        "log": str(log_path),
        "status": "success",
    }
