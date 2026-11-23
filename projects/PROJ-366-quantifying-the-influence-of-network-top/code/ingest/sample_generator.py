"""
Sample Generator Module

Generates N=10 pre-equilibrated amorphous silicon configurations using ASE.
This module creates realistic supercells by melting and quenching crystalline silicon
using the Stillinger-Weber potential, simulating the amorphization process.
"""
import os
import sys
import time
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

try:
    from ase import Atoms
    from ase.build import bulk
    from ase.calculators.lammpsrun import LAMMPS
    from ase.io import write, read
    from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
    from ase.md.langevin import Langevin
    from ase.units import ps, K, eV
except ImportError:
    print("ERROR: ASE and LAMMPS dependencies are required. Install with: pip install ase")
    print("Ensure LAMMPS is installed and available in PATH.")
    sys.exit(1)

from config import get_config, get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_lammps_executable() -> str:
    """
    Finds the LAMMPS executable in the system PATH.

    Returns:
        Path to the LAMMPS executable.

    Raises:
        RuntimeError: If LAMMPS is not found.
    """
    lammps_exe = os.environ.get('LAMMPS_EXE', 'lmp')
    try:
        subprocess.run([lammps_exe, '-version'], check=True, capture_output=True)
        return lammps_exe
    except subprocess.CalledProcessError:
        raise RuntimeError(f"LAMMPS executable '{lammps_exe}' not found. Please set LAMMPS_EXE environment variable or ensure 'lmp' is in PATH.")


def create_initial_crystal(n_atoms: int = 1000) -> Atoms:
    """
    Creates a crystalline silicon supercell with approximately n_atoms.

    Args:
        n_atoms: Target number of atoms (will be adjusted to nearest supercell).

    Returns:
        ASE Atoms object representing the crystal.
    """
    # Diamond cubic silicon
    si_bulk = bulk('Si', 'diamond', a=5.43)

    # Calculate supercell size
    n_unit_cells = int((n_atoms / len(si_bulk)) ** (1/3))
    supercell = si_bulk * (n_unit_cells, n_unit_cells, n_unit_cells)

    logger.info(f"Created crystal supercell with {len(supercell)} atoms "
                f"({n_unit_cells}x{n_unit_cells}x{n_unit_cells} unit cells)")

    return supercell


def generate_lammps_input_script(work_dir: Path, potential_file: str) -> Path:
    """
    Generates a LAMMPS input script for melt-and-quench simulation.

    Args:
        work_dir: Directory to write the input script.
        potential_file: Path to the Stillinger-Weber potential file.

    Returns:
        Path to the generated input script.
    """
    input_script = work_dir / "melt_quench.in"

    script_content = f"""
    # Melt and Quench Simulation for Amorphous Silicon
    units           metal
    atom_style      atomic
    boundary        p p p

    # Read initial configuration
    read_data       data.silicon

    # Define Stillinger-Weber potential
    pair_style      sw
    pair_coeff      * * {potential_file} Si

    # Equilibration at high temperature (melting)
    velocity        all create 2000.0 12345
    fix             1 all nvt temp 2000.0 2000.0 0.1
    run             5000

    # Quench to room temperature
    fix             2 all nvt temp 2000.0 300.0 0.1
    run             10000

    # Final equilibration at 300K
    fix             3 all npt temp 300.0 300.0 0.1 iso 0.0 0.0 1.0
    run             5000

    # Write final configuration
    write_data      data.amorphous
    write_dump      all atom final.xyz type yes
    """

    with open(input_script, 'w') as f:
        f.write(script_content)

    logger.info(f"Generated LAMMPS input script: {input_script}")
    return input_script


def melt_and_quench(initial_atoms: Atoms, work_dir: Path, potential_file: str) -> Atoms:
    """
    Performs a melt-and-quench simulation to generate amorphous silicon.

    Args:
        initial_atoms: Initial crystalline structure.
        work_dir: Working directory for simulation.
        potential_file: Path to SW potential file.

    Returns:
        ASE Atoms object of the amorphous structure.
    """
    work_dir.mkdir(parents=True, exist_ok=True)

    # Write initial data file
    data_file = work_dir / "data.silicon"
    initial_atoms.write(data_file, format='lammps-data')

    # Generate input script
    input_script = generate_lammps_input_script(work_dir, potential_file)

    # Run LAMMPS
    lammps_exe = get_lammps_executable()
    cmd = [lammps_exe, '-in', str(input_script)]

    logger.info(f"Running LAMMPS simulation in {work_dir}...")
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per sample
        )

        if result.returncode != 0:
            logger.error(f"LAMMPS simulation failed:\n{result.stderr}")
            raise RuntimeError("LAMMPS simulation failed")

        elapsed = time.time() - start_time
        logger.info(f"LAMMPS simulation completed in {elapsed:.2f} seconds")

    except subprocess.TimeoutExpired:
        logger.error("LAMMPS simulation timed out")
        raise RuntimeError("LAMMPS simulation timed out")

    # Read final configuration
    final_data = work_dir / "data.amorphous"
    if not final_data.exists():
        raise RuntimeError("Final data file not generated by LAMMPS")

    final_atoms = read(final_data, format='lammps-data')
    logger.info(f"Generated amorphous structure with {len(final_atoms)} atoms")

    return final_atoms


def generate_samples(n_samples: int = 10, atoms_per_sample: int = 1000, output_dir: Path = None) -> List[Path]:
    """
    Generates N pre-equilibrated amorphous silicon samples.

    Args:
        n_samples: Number of samples to generate.
        atoms_per_sample: Target atoms per sample.
        output_dir: Directory to save XYZ files.

    Returns:
        List of paths to generated XYZ files.
    """
    if output_dir is None:
        config = get_config()
        paths = get_paths()
        output_dir = paths['raw_data']

    output_dir.mkdir(parents=True, exist_ok=True)

    # Try to find SW potential file
    potential_file = os.environ.get('SW_POTENTIAL', 'Si.sw')
    if not os.path.exists(potential_file):
        # Common LAMMPS potential location
        potential_file = '/usr/share/lammps/potentials/Si.sw'
        if not os.path.exists(potential_file):
            raise FileNotFoundError(
                f"Stillinger-Weber potential file not found. "
                f"Please set SW_POTENTIAL environment variable or place 'Si.sw' in current directory."
            )

    generated_files = []

    for i in range(n_samples):
        sample_id = f"sample_{i+1:02d}"
        work_dir = output_dir / "work" / sample_id
        output_file = output_dir / f"{sample_id}.xyz"

        if output_file.exists():
            logger.info(f"Sample {sample_id} already exists, skipping...")
            generated_files.append(output_file)
            continue

        logger.info(f"Generating sample {i+1}/{n_samples}: {sample_id}")

        try:
            # Create initial crystal
            crystal = create_initial_crystal(atoms_per_sample)

            # Melt and quench
            amorphous = melt_and_quench(crystal, work_dir, potential_file)

            # Write XYZ file
            write(output_file, amorphous, format='xyz')

            generated_files.append(output_file)
            logger.info(f"Successfully generated: {output_file}")

        except Exception as e:
            logger.error(f"Failed to generate sample {sample_id}: {e}")
            # Clean up work directory on failure
            import shutil
            if work_dir.exists():
                shutil.rmtree(work_dir)
            raise

    logger.info(f"Generated {len(generated_files)} samples in {output_dir}")
    return generated_files


def main():
    """
    Main entry point for sample generation.
    """
    config = get_config()
    paths = get_paths()

    n_samples = 10
    atoms_per_sample = 1000

    logger.info(f"Starting sample generation: {n_samples} samples, {atoms_per_sample} atoms each")

    try:
        generated = generate_samples(n_samples, atoms_per_sample, paths['raw_data'])
        logger.info(f"SUCCESS: Generated {len(generated)} samples")
        return 0
    except Exception as e:
        logger.error(f"FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())