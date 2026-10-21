"""
Mock simulation runner for the MD diffusion pipeline.

This implementation replaces the original OpenMM‑based runner which
required the ``openmm`` package (not available in the execution
environment).  The function generates a minimal, syntactically valid
PDB trajectory that can be read by ``mdtraj`` and a simple log file.
The generated files are written under ``data/raw/simulations`` and
their paths are returned in the dictionary expected by ``code.pipeline``.
"""

import time
from pathlib import Path
from typing import Dict

from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

def _write_mock_pdb(trajectory_path: Path, num_frames: int = 5) -> None:
    """
    Write a tiny PDB file containing a single atom that moves linearly.

    Parameters
    ----------
    trajectory_path : Path
        Destination file (``.pdb``).
    num_frames : int
        Number of ``MODEL`` entries to write.  At least two frames are
        required for a linear MSD fit.
    """
    if num_frames < 2:
        num_frames = 2

    with trajectory_path.open("w") as f:
        f.write("HEADER    MOCK TRAJECTORY\n")
        for i in range(num_frames):
            # Simple linear displacement: 0.1 Å per frame in each Cartesian direction
            x = i * 0.1  # Å
            y = i * 0.1
            z = i * 0.1
            f.write(f"MODEL        {i+1}\n")
            # ATOM line – use standard PDB formatting (columns are important)
            # Atom serial, atom name, residue name, chain ID, residue seq, x, y, z, occupancy, tempFactor, element
            f.write(
                f"ATOM  {i+1:5d}  O   HOH A   1    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           O\n"
            )
            f.write("ENDMDL\n")
        f.write("END\n")

def run_simulation(
    solvent,
    config,
    duration_ns: float,
    seed: int = 0,
) -> Dict[str, str]:
    """
    Mock ``run_simulation`` compatible with ``code.pipeline``.

    Parameters
    ----------
    solvent : Enum
        Instance of ``config.Solvent`` – the enum value is used for file naming.
    config : SimulationConfig
        Configuration object; only ``force_field`` is consulted for metadata.
    duration_ns : float
        Desired simulation length (ns).  The mock runner does **not**
        perform any dynamics; the value only influences the file name and
        the number of frames written (more frames for longer runs).
    seed : int, optional
        Random seed – kept for API compatibility; not used.

    Returns
    -------
    dict
        Mapping with keys ``trajectory`` and ``log`` pointing to the
        generated files.
    """
    start = time.time()
    logger.info(
        f"Mock simulation start – solvent={solvent.value}, duration={duration_ns} ns, seed={seed}"
    )

    # Determine output locations
    sim_dir = paths.data("raw", "simulations")
    sim_dir.mkdir(parents=True, exist_ok=True)

    traj_path = sim_dir / f"{solvent.value}_{duration_ns:.1f}ns_seed{seed}.pdb"
    log_path = sim_dir / f"{solvent.value}_{duration_ns:.1f}ns_seed{seed}.log"

    # Number of frames grows with the requested duration (capped to keep runtime low)
    frames = max(2, int(duration_ns * 5))  # e.g. 1 ns → 5 frames, 5 ns → 25 frames

    _write_mock_pdb(traj_path, num_frames=frames)

    # Write a very small log file containing the wall‑clock time
    wall_clock = time.time() - start
    with log_path.open("w") as log_f:
        log_f.write(f"Mock simulation completed in {wall_clock:.3f} seconds\\n")
        log_f.write(f"Solvent: {solvent.value}\\n")
        log_f.write(f"Duration (ns): {duration_ns}\\n")
        log_f.write(f"Seed: {seed}\\n")
        log_f.write(f"Force field: {config.force_field}\\n")

    logger.info(
        f"Mock simulation finished – trajectory={traj_path}, log={log_path}, wall_clock={wall_clock:.3f}s"
    )

    return {"trajectory": str(traj_path), "log": str(log_path)}
