"""
Sample Generator for Amorphous Silicon.

Generates N=10 pre-equilibrated amorphous silicon supercells (>=1000 atoms each)
using the Atomic Simulation Environment (ASE) and LAMMPS via the 'ase-lammps' interface.

Strategy:
1. Start with a crystalline Si diamond cubic structure.
2. Melt it at high temperature (e.g., 4000K) to randomize positions.
3. Quench it rapidly to 300K to form an amorphous phase.
4. Equilibrate at 300K.
5. Save the final configuration as XYZ.

Requires:
- ase
- lammps (must be installed and accessible in PATH or specified via LAMMPS_EXEC)
- numpy

Output: 10 XYZ files in data/raw/ named sample_00.xyz to sample_09.xyz.
"""
import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

import numpy as np
from ase import Atoms
from ase.build import bulk
from ase.io import write, read
from ase.calculators.lammpsrun import LAMMPS
from ase.units import eV, K, ps, kb

# Project imports
from config import get_config, get_paths

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SI_DENSITY = 2.33  # g/cm^3 for Si
ATOMIC_MASS_SI = 28.0855  # g/mol

def get_lammps_executable() -> str:
    """Get LAMMPS executable path from environment or config."""
    config = get_config()
    if 'LAMMPS' in config.get('simulation', {}):
        return config['simulation']['LAMMPS']
    # Fallback to environment variable or 'lammps'
    return os.environ.get('LAMMPS_EXEC', 'lammps')

def create_initial_crystal(n_atoms: int = 1000) -> Atoms:
    """Create a crystalline Si supercell with approximately n_atoms."""
    # Diamond cubic Si lattice constant ~ 5.43 Angstroms
    a = 5.43
    # Unit cell has 8 atoms
    # Calculate scaling factor to get close to n_atoms
    # n_atoms = 8 * n^3 => n = (n_atoms / 8)^(1/3)
    n_cells = int(np.round((n_atoms / 8.0) ** (1.0/3.0)))
    if n_cells < 2:
        n_cells = 2
    
    # Create bulk
    si_crystal = bulk('Si', 'diamond', a=a)
    # Replicate
    si_super = si_crystal * (n_cells, n_cells, n_cells)
    
    # Adjust to exact n_atoms if needed by adding/removing atoms (rarely needed)
    # For this task, we accept the nearest supercell size >= 1000
    logger.info(f"Created crystal with {len(si_super)} atoms (target: {n_atoms})")
    return si_super

def melt_and_quench(atoms: Atoms, temp_start: float = 4000.0, temp_end: float = 300.0, 
                    time_step: float = 0.5, n_steps_melt: int = 5000, 
                    n_steps_quench: int = 10000, n_steps_eq: int = 5000) -> Atoms:
    """
    Perform a melt-quench-equilibration cycle using LAMMPS.
    
    Steps:
    1. NVT Melt at temp_start for n_steps_melt.
    2. NVT Quench from temp_start to temp_end over n_steps_quench.
    3. NVT Equilibrate at temp_end for n_steps_eq.
    
    Returns the final Atoms object.
    """
    lmp_exec = get_lammps_executable()
    
    # Define potential file path (Standard SW potential for Si)
    # We assume the potential file 'Si.sw' is in the project root or data/raw
    # If not found, we might need to download it or use a default path.
    # For robustness, we try common locations.
    potential_paths = [
        Path('data/raw/Si.sw'),
        Path('code/simulation/Si.sw'),
        Path('Si.sw'),
        Path(os.path.expanduser('~/.lammps/potentials/Si.sw'))
    ]
    
    pot_file = None
    for p in potential_paths:
        if p.exists():
            pot_file = str(p)
            break
    
    if not pot_file:
        # If no potential found, we cannot proceed with real LAMMPS.
        # Per constraints, we must fail loudly, not fake it.
        raise FileNotFoundError(
            "LAMMPS Si.sw potential file not found. "
            "Please ensure 'Si.sw' exists in data/raw/ or code/simulation/."
        )
    
    # Create LAMMPS calculator
    # We use a temporary directory for LAMMPS runs
    run_dir = Path('data/raw/lammps_runs')
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize calculator
    # Note: ase-lammps requires the 'pair_style' and 'pair_coeff' to be set via input script
    # or by passing them to the calculator if supported. 
    # We will generate an input script for full control.
    
    # Instead of using the calculator directly for the complex cycle,
    # we will write a custom LAMMPS input script and run it.
    
    input_script_path = run_dir / 'melt_quench.in'
    data_file_path = run_dir / 'data.si'
    dump_file_path = run_dir / 'dump.xyz'
    
    # Write initial structure to LAMMPS data format
    write(data_file_path, atoms, format='lammps-data', order=['id', 'type', 'x', 'y', 'z'])
    
    # Generate LAMMPS input script
    script_content = f"""
    # Melt-Quench-Equilibrium Script for Amorphous Si
    units metal
    atom_style atomic
    boundary p p p
    
    read_data {data_file_path}
    
    # Potential
    pair_style sw
    pair_coeff * * {pot_file} Si
    
    # Neighbor settings
    neighbor 0.3 bin
    neigh_modify delay 0 every 1 check yes
    
    # Melt Phase (NVT)
    velocity all create {temp_start} 12345 rot yes
    fix 1 all nvt temp {temp_start} {temp_start} 0.1
    run {n_steps_melt}
    unfix 1
    
    # Quench Phase (NVT)
    fix 2 all nvt temp {temp_start} {temp_end} 0.1
    run {n_steps_quench}
    unfix 2
    
    # Equilibrium Phase (NVT)
    fix 3 all nvt temp {temp_end} {temp_end} 0.1
    run {n_steps_eq}
    unfix 3
    
    # Dump final structure
    dump 1 all custom 1 {dump_file_path} id type x y z
    run 0
    """
    
    with open(input_script_path, 'w') as f:
        f.write(script_content)
    
    logger.info(f"Running LAMMPS melt-quench in {run_dir}")
    
    # Run LAMMPS
    cmd = [lmp_exec, '-in', str(input_script_path)]
    try:
        result = subprocess.run(cmd, cwd=str(run_dir), check=True, capture_output=True, text=True)
        # logger.debug(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
    except subprocess.CalledProcessError as e:
        logger.error(f"LAMMPS execution failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise RuntimeError("LAMMPS simulation failed.")
    
    # Read result
    if not dump_file_path.exists():
        raise RuntimeError("LAMMPS did not produce the dump file.")
    
    final_atoms = read(dump_file_path, index=-1) # Read last frame
    logger.info(f"Simulation complete. Final atoms: {len(final_atoms)}")
    
    return final_atoms

def generate_samples(n_samples: int = 10, min_atoms: int = 1000, output_dir: str = 'data/raw') -> List[str]:
    """
    Generate N pre-equilibrated amorphous silicon samples.
    
    Args:
        n_samples: Number of samples to generate.
        min_atoms: Minimum number of atoms per sample.
        output_dir: Directory to save XYZ files.
    
    Returns:
        List of paths to generated XYZ files.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    for i in range(n_samples):
        sample_id = f"sample_{i:02d}"
        xyz_path = output_path / f"{sample_id}.xyz"
        
        if xyz_path.exists():
            logger.warning(f"File {xyz_path} already exists. Skipping generation.")
            generated_files.append(str(xyz_path))
            continue
        
        logger.info(f"Generating sample {i+1}/{n_samples}: {sample_id}")
        
        try:
            # 1. Create initial crystal
            atoms = create_initial_crystal(min_atoms)
            
            # 2. Melt-Quench-Equilibrate
            # Add a small random displacement to break symmetry if needed, 
            # but LAMMPS velocity create usually handles this.
            final_atoms = melt_and_quench(atoms)
            
            # 3. Save to XYZ
            write(str(xyz_path), final_atoms)
            generated_files.append(str(xyz_path))
            logger.info(f"Successfully saved {xyz_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate sample {sample_id}: {e}")
            # Do not create a fake file. Raise or skip.
            # Per constraint: "If the task asks for a dataset, produce the real file."
            # If we can't produce it, we must fail loudly.
            raise RuntimeError(f"Sample generation failed for {sample_id}. Aborting task.") from e
        
        # Small delay to avoid overwhelming the system if running sequentially
        time.sleep(0.1)
    
    return generated_files

def main():
    """Main entry point for sample generation."""
    config = get_config()
    n_samples = config.get('ingest', {}).get('n_samples', 10)
    min_atoms = config.get('ingest', {}).get('min_atoms', 1000)
    output_dir = get_paths()['raw_data']
    
    logger.info(f"Starting sample generation: N={n_samples}, MinAtoms={min_atoms}")
    
    files = generate_samples(n_samples=n_samples, min_atoms=min_atoms, output_dir=output_dir)
    
    if len(files) != n_samples:
        raise RuntimeError(f"Expected {n_samples} files, but generated {len(files)}.")
    
    logger.info(f"Successfully generated {len(files)} samples.")
    
    # Verification
    for f in files:
        atoms = read(f)
        if len(atoms) < min_atoms:
            raise ValueError(f"Sample {f} has {len(atoms)} atoms, less than required {min_atoms}.")
    
    logger.info("All samples verified.")

if __name__ == "__main__":
    main()
