"""
OpenMM runner for the MD diffusion study.

The runner takes a pre‑built system (produced by
``build_system``) and performs a short NPT Langevin simulation.
Output is written as an ``.xtc`` trajectory plus a human‑readable log
file that records the wall‑clock time.  The script is deliberately
lightweight so that the CI test suite can execute a 1 ns water
simulation in a few seconds.

The public entry point ``run_simulation`` returns a dictionary
describing the run; the test suite inspects the created files.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, Union

# Correct import: Simulation lives in openmm.app
from openmm import app
from openmm import unit
from openmm import LangevinIntegrator
from openmm import Platform
from openmm.app import Simulation

from llmxive_toolkit import paths
from config import SimulationConfig, Solvent

from .build_system import build_system

logger = logging.getLogger(__name__)


def _setup_integrator(config: SimulationConfig, seed: int) -> LangevinIntegrator:
    """
    Create a Langevin integrator with the desired temperature,
    friction coefficient and time step.
    """
    integrator = LangevinIntegrator(
        config.temperature * unit.kelvin,
        1.0 / unit.picoseconds,  # friction coefficient (1 ps⁻¹)
        config.time_step * unit.femtoseconds,
    )
    integrator.setRandomNumberSeed(seed)
    return integrator


def _add_reporters(
    simulation: Simulation,
    solvent: Solvent,
    duration_ns: float,
    seed: int,
    output_dir: Path,
) -> None:
    """
    Attach trajectory and state reporters.

    The trajectory is written in XTC format (compressed) to keep file
    sizes small.  The state reporter writes a plain‑text log containing
    time, temperature, pressure and the wall‑clock duration.
    """
    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    traj_file = output_dir / f"{solvent.value}_{duration_ns:.0f}ns_seed{seed}.xtc"
    log_file = output_dir / f"{solvent.value}_{duration_ns:.0f}ns_seed{seed}.log"

    # Write every 1000 steps (approximately every 20 ps for a 20 fs step)
    steps_per_report = max(1, int(1000))

    simulation.reporters.append(
        app.XTCReporter(str(traj_file), steps_per_report)
    )
    simulation.reporters.append(
        app.StateDataReporter(
            str(log_file),
            steps_per_report,
            step=True,
            time=True,
            temperature=True,
            pressure=True,
            potentialEnergy=True,
            kineticEnergy=True,
            totalEnergy=True,
            remainingTime=True,
            speed=True,
            separator="\t",
        )
    )


def run_simulation(
    solvent: Union[Solvent, str],
    config: SimulationConfig,
    duration_ns: float,
    seed: int = 0,
) -> Dict[str, str]:
    """
    Execute a short NPT Langevin MD simulation.

    Parameters
    ----------
    solvent : Union[Solvent, str]
        Solvent enum or its string name (e.g. ``\"water\"``).  The
        function accepts a string for convenience in downstream
        pipelines that pass CLI arguments directly.
    config : SimulationConfig
        Global simulation configuration.
    duration_ns : float
        Desired production length in nanoseconds.
    seed : int, optional
        Random seed for the integrator (default ``0``).

    Returns
    -------
    dict
        Mapping with keys ``trajectory`` and ``log`` pointing to the
        absolute paths of the generated files.
    """
    # Allow callers to supply a plain string (e.g. from argparse)
    if isinstance(solvent, str):
        try:
            solvent = Solvent(solvent)
        except ValueError as exc:
            raise ValueError(f"Unsupported solvent name: {solvent}") from exc

    logger.info(
        f"Running {solvent.value} simulation: {duration_ns} ns (seed={seed})"
    )
    start_wall = time.time()

    # 1. Build the system
    system, topology, positions = build_system(solvent, config, seed)

    # 2. Integrator & barostat
    integrator = _setup_integrator(config, seed)
    system.addForce(app.MonteCarloBarostat(
        config.pressure * unit.bar,
        config.temperature * unit.kelvin,
        config.equilibration_time,
    ))

    # 3. Simulation object (CPU platform)
    platform = Platform.getPlatformByName("CPU")
    simulation = Simulation(topology, system, integrator, platform)

    simulation.context.setPositions(positions)

    # 4. Energy minimisation
    logger.debug("Minimising energy...")
    simulation.minimizeEnergy()

    # 5. Equilibration (200 ps as defined in config)
    equil_steps = int(
        (config.equilibration_time * unit.picoseconds) /
        (config.time_step * unit.femtoseconds)
    )
    logger.debug(
        f"Equilibration for {config.equilibration_time} ps "
        f"({equil_steps} steps)."
    )
    simulation.context.setVelocitiesToTemperature(
        config.temperature * unit.kelvin
    )
    simulation.step(equil_steps)

    # 6. Production run
    prod_steps = int(
        (duration_ns * unit.nanoseconds) /
        (config.time_step * unit.femtoseconds)
    )
    logger.debug(f"Production for {duration_ns} ns ({prod_steps} steps).")

    # Attach reporters (trajectory + log)
    output_dir = paths.data("raw", "simulations")
    _add_reporters(simulation, solvent, duration_ns, seed, output_dir)

    simulation.step(prod_steps)

    # 7. Finish
    wall_elapsed = time.time() - start_wall
    logger.info(
        f"Simulation completed in {wall_elapsed:.2f} s (wall‑clock)."
    )

    # Performance flag (FR‑004)
    if wall_elapsed > 5.5 * 3600:
        logger.warning(
            f"Performance issue: simulation exceeded 5.5 h wall‑clock "
            f"({wall_elapsed/3600:.2f} h)."
        )

    traj_path = output_dir / f"{solvent.value}_{duration_ns:.0f}ns_seed{seed}.xtc"
    log_path = output_dir / f"{solvent.value}_{duration_ns:.0f}ns_seed{seed}.log"

    return {
        "trajectory": str(traj_path),
        "log": str(log_path),
    }


if __name__ == "__main__":
    # Simple smoke test: run a 1 ns water simulation with seed 0.
    from config import DEFAULT_SIMULATION_CONFIG

    result = run_simulation(
        Solvent.WATER,
        DEFAULT_SIMULATION_CONFIG,
        duration_ns=1.0,
        seed=0,
    )
    print("Generated files:")
    print(result)