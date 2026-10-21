"""
Real OpenMM simulation runner for the MD diffusion pipeline.

This module executes a full NPT simulation: minimization, equilibration,
and production. Trajectories are written as .xtc files using mdtraj.
"""

import time
import logging
from pathlib import Path
from typing import Dict

import mdtraj as md
from openmm import app, unit, Platform
from openmm import LangevinMiddleIntegrator, MonteCarloBarostat

from llmxive_toolkit import paths, get_logger
from .build_system import build_system

logger = get_logger(__name__)

def run_simulation(
    solvent,
    config,
    duration_ns: float,
    seed: int = 0,
) -> Dict[str, str]:
    """
    Run a seeded NPT Langevin simulation using OpenMM on the CPU.
    """
    start_wall = time.time()
    logger.info(f"Real simulation start: {solvent.value}, {duration_ns}ns, seed={seed}")

    # 1. Build System
    system, topology, positions = build_system(solvent, config, seed)

    # 2. Setup Simulation
    # Pinned temperature and pressure
    temp = 298.15 * unit.kelvin
    pressure = 1.0 * unit.bar
    timestep = 2.0 * unit.femtoseconds
    
    integrator = LangevinMiddleIntegrator(temp, 1.0 / unit.picosecond, timestep)
    integrator.setRandomSeed(seed)
    
    # Add Barostat for NPT
    system.addForce(MonteCarloBarostat(pressure, temp))

    # Force CPU platform
    platform = Platform.getPlatformByName('CPU')
    simulation = app.Simulation(topology, system, integrator, platform)
    simulation.context.setPositions(positions)

    # Output paths
    sim_dir = paths.data("raw", "simulations")
    sim_dir.mkdir(parents=True, exist_ok=True)
    traj_xtc = sim_dir / f"{solvent.value}_{duration_ns:.1f}ns_seed{seed}.xtc"
    log_path = sim_dir / f"{solvent.value}_{duration_ns:.1f}ns_seed{seed}.log"
    tmp_dcd = sim_dir / f"tmp_{seed}.dcd"
    tmp_pdb = sim_dir / f"tmp_{seed}.pdb"

    # 3. Minimization
    logger.info("Minimizing energy...")
    simulation.minimizeEnergy()

    # 4. Equilibration (short NPT)
    logger.info("Equilibrating...")
    simulation.step(500)

    # 5. Production
    logger.info(f"Running production for {duration_ns} ns...")
    # Save initial structure for mdtraj
    with open(tmp_pdb, "w") as f:
        app.PDBFile.writeFile(simulation.topology, simulation.context.getState(getPositions=True).getPositions(), f)

    # OpenMM native DCD reporter
    simulation.reporters.append(app.DCDReporter(str(tmp_dcd), 1000))
    
    steps = int((duration_ns * unit.nanoseconds) / timestep)
    simulation.step(steps)

    # 6. Convert DCD to XTC using mdtraj
    logger.info("Converting trajectory to XTC...")
    traj = md.load(str(tmp_dcd), top=str(tmp_pdb))
    traj.save_xtc(str(traj_xtc))

    # Cleanup temporary files
    tmp_dcd.unlink(missing_ok=True)
    tmp_pdb.unlink(missing_ok=True)

    # Wall-clock logging
    end_wall = time.time()
    wall_clock = end_wall - start_wall
    
    with log_path.open("w") as log_f:
        log_f.write(f"Wall-clock time: {wall_clock:.3f} seconds\n")
        log_f.write(f"Solvent: {solvent.value}\n")
        log_f.write(f"Duration: {duration_ns} ns\n")
        log_f.write(f"Seed: {seed}\n")
        if wall_clock > 5.5 * 3600:
            log_f.write("PERFORMANCE ISSUE: Run exceeded 5.5 hours\n")

    logger.info(f"Simulation finished. Wall-clock: {wall_clock:.3f}s")
    return {"trajectory": str(traj_xtc), "log": str(log_path)}
