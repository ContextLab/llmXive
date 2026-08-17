"""
DFTB+ Calculator for geometry optimization and descriptor extraction.

This module invokes the DFTB+ external binary to perform semi-empirical
quantum mechanical calculations on individual molecules. It handles:
1. Preparation of DFTB+ input files (geometry, parameters).
2. Execution of the DFTB+ binary.
3. Parsing of output files for HOMO, LUMO, and Mayer bond orders.
4. Unit normalization (conversion to eV).
5. Error handling for convergence and OOM failures.
"""
import os
import re
import subprocess
import sys
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import shared utilities from the project
from utils.error_utils import ConvergenceError, OOMError, detect_convergence_failure, check_oom_in_log
from utils.logging_utils import log_dftb_invocation, log_resource_snapshot

# Constants
DFTB_BINARY = "dftb+"
DEFAULT_MAX_CYCLES = 100
GEOMETRY_OPTIMIZER = "GeometricOptimiser"
# DFTB+ default energy unit is Hartree; we need eV.
# 1 Hartree = 27.211386245988 eV
HARTREE_TO_EV = 27.211386245988

# Setup logger
logger = logging.getLogger(__name__)


def smiles_to_xyz(smiles: str, output_path: Path) -> None:
    """
    Convert a SMILES string to an XYZ file using RDKit.
    This is a prerequisite for DFTB+ input.
    
    Args:
        smiles: The SMILES string of the molecule.
        output_path: Path where the XYZ file will be written.
        
    Raises:
        ValueError: If SMILES is invalid or RDKit fails to generate 3D coordinates.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError:
        logger.error("RDKit is required for SMILES to XYZ conversion but is not installed.")
        raise

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: {smiles}")

    # Add hydrogens
    mol = Chem.AddHs(mol)
    
    # Generate 3D coordinates
    # Using ETKDG for better conformation generation
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    success = AllChem.EmbedMolecule(mol, params)
    
    if success == -1:
        # Fallback to basic embedding if ETKDG fails
        success = AllChem.EmbedMolecule(mol)
    
    if success == -1:
        raise ValueError(f"Failed to generate 3D coordinates for SMILES: {smiles}")

    # Optimize geometry with MMFF94 to give DFTB a better starting point
    mmff_props = AllChem.MMFFGetMoleculeProperties(mol)
    if mmff_props is not None:
        ff = AllChem.MMFFGetMoleculeForceField(mol, mmff_props)
        if ff is not None:
            ff.Minimize(maxIts=200)

    # Write XYZ file
    writer = Chem.SDWriter(str(output_path))
    writer.SetWedgeBondMode(False)
    # RDKit SDWriter writes SD format, we need XYZ. 
    # Let's manually write XYZ to ensure format correctness.
    
    conf = mol.GetConformer()
    natoms = mol.GetNumAtoms()
    with open(output_path, 'w') as f:
        f.write(f"{natoms}\n")
        f.write(f"DFTB+ Generated from {smiles}\n")
        for i in range(natoms):
            atom = mol.GetAtomWithIdx(i)
            pos = conf.GetAtomPosition(i)
            f.write(f"{atom.GetSymbol():<3} {pos.x:15.6f} {pos.y:15.6f} {pos.z:15.6f}\n")


def create_dftb_input(
    xyz_path: Path,
    work_dir: Path,
    max_cycles: int = DEFAULT_MAX_CYCLES,
    method: str = "GFN2-xTB"
) -> Dict[str, Path]:
    """
    Create DFTB+ input files (geometry.gen, dftb_in.hsd, hamiltonian/params).
    
    Args:
        xyz_path: Path to the input XYZ file.
        work_dir: Working directory for DFTB+ execution.
        max_cycles: Maximum optimization cycles.
        method: The DFTB method (e.g., 'GFN2-xTB', 'GFN1-xTB').
        
    Returns:
        A dictionary of created file paths.
    """
    # Copy geometry to geometry.gen (DFTB+ standard input name)
    geo_file = work_dir / "geometry.gen"
    shutil.copy(xyz_path, geo_file)
    
    # Create dftb_in.hsd
    hsd_content = f"""
Geometry = FromFile
  Filename = "geometry.gen"
  ForceScheme = "BFGS"
  MaxCycles = {max_cycles}
  WriteEnergies = Yes
  WriteCharges = Yes
  WriteBonds = Yes
  WriteOrbitals = Yes

Hamiltonian = {method}
  # Standard parameters for GFN2-xTB
  # Charge = 0.0
  # SpinPolarisation = None

Output = Yes
  BondOrderMatrix = Yes
  MolecularOrbitals = Yes
"""
    hsd_path = work_dir / "dftb_in.hsd"
    with open(hsd_path, 'w') as f:
        f.write(hsd_content)

    # Note: For GFN2-xTB, DFTB+ usually downloads parameters automatically 
    # if the 'uploaddir' is set or if using the dftb+ package with parameters.
    # We assume the environment has the necessary parameters or auto-download works.
    # If a specific parameter directory is needed, it should be configured in the environment.
    
    return {
        "geometry": geo_file,
        "hsd": hsd_path
    }


def run_dftb_work(work_dir: Path, timeout: int = 3600) -> Tuple[int, str]:
    """
    Execute the DFTB+ binary in the specified working directory.
    
    Args:
        work_dir: Directory containing dftb_in.hsd and geometry.gen.
        timeout: Maximum execution time in seconds.
        
    Returns:
        Tuple of (exit_code, stdout_stderr_combined)
        
    Raises:
        OOMError: If out-of-memory is detected.
        ConvergenceError: If convergence failure is detected.
        RuntimeError: If DFTB+ crashes or times out.
    """
    cmd = [DFTB_BINARY]
    logger.info(f"Executing DFTB+ in {work_dir}: {' '.join(cmd)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )
    except subprocess.TimeoutExpired as e:
        logger.error(f"DFTB+ timed out after {timeout}s")
        raise RuntimeError(f"DFTB+ execution timed out after {timeout}s") from e
    except FileNotFoundError:
        logger.error(f"DFTB+ binary '{DFTB_BINARY}' not found in PATH.")
        raise RuntimeError(f"DFTB+ binary '{DFTB_BINARY}' not found.")
    
    duration = time.time() - start_time
    log_resource_snapshot(duration)
    
    stdout = result.stdout
    stderr = result.stderr
    combined = stdout + stderr
    
    # Check for OOM
    if check_oom_in_log(combined):
        logger.error("OOM detected in DFTB+ output.")
        raise OOMError("DFTB+ process ran out of memory.")
    
    # Check for convergence failure
    if detect_convergence_failure(combined):
        logger.error("Convergence failure detected in DFTB+ output.")
        raise ConvergenceError("DFTB+ geometry optimization did not converge.")
    
    if result.returncode != 0:
        logger.warning(f"DFTB+ returned non-zero exit code: {result.returncode}")
        # Check if it's a specific non-critical warning or a hard fail
        # For now, treat non-zero as a failure unless we have specific logic to ignore it
        # But we already checked OOM/Convergence, so this might be a missing parameter issue
        if "Error" in combined or "Fatal" in combined:
            raise RuntimeError(f"DFTB+ execution failed: {combined}")
    
    return result.returncode, combined


def parse_dftb_output(work_dir: Path) -> Dict[str, Any]:
    """
    Parse DFTB+ output files to extract HOMO, LUMO, and Mayer bond orders.
    
    Expected outputs:
    - dftb_out: Main output log.
    - charges.bin: (Optional) Charge information.
    - bondorder.bin: (Optional) Mayer bond orders.
    - molecular_orbitals.bin: (Optional) Orbital energies.
    
    Args:
        work_dir: Directory where DFTB+ ran.
        
    Returns:
        Dictionary with keys:
            - homo_energy (float): HOMO energy in eV.
            - lumo_energy (float): LUMO energy in eV.
            - mayer_bond_orders (list): List of (atom1, atom2, order).
            - total_energy (float): Total energy in eV.
            
    Raises:
        ValueError: If required output files are missing or parsing fails.
    """
    dftb_out = work_dir / "dftb_out"
    if not dftb_out.exists():
        raise ValueError("dftb_out file not found. DFTB+ may not have run successfully.")
    
    with open(dftb_out, 'r') as f:
        content = f.read()
    
    # Parse HOMO/LUMO from dftb_out
    # DFTB+ typically prints eigenvalues in a table. We need to find the highest occupied and lowest unoccupied.
    # The output format varies slightly by version, but usually looks like:
    #   Orbital  Energy (Hartree)  Occupancy
    #   ...
    # We look for the section "Orbital energies" or similar.
    
    homo_ev = None
    lumo_ev = None
    total_energy_ev = None
    
    # Extract Total Energy
    # Pattern: "Total energy = -XXX.XXXXXXX Hartree"
    energy_match = re.search(r"Total energy\s*=\s*([-+]?\d*\.\d+|\d+)\s*Hartree", content)
    if energy_match:
        total_energy_ev = float(energy_match.group(1)) * HARTREE_TO_EV
    
    # Extract Eigenvalues
    # We need to find the list of orbital energies.
    # DFTB+ output usually has a block like:
    # Orbital energies (Hartree):
    #   1  -0.50000000
    #   2  -0.45000000
    # ...
    # We need to determine the number of electrons to find HOMO.
    
    # Alternative: Look for "Highest Occupied" and "Lowest Unoccupied" if printed explicitly
    # Some versions print:
    # "HOMO energy = -X.XX Hartree"
    # "LUMO energy = -X.XX Hartree"
    
    homo_match = re.search(r"HOMO energy\s*=\s*([-+]?\d*\.\d+|\d+)", content)
    lumo_match = re.search(r"LUMO energy\s*=\s*([-+]?\d*\.\d+|\d+)", content)
    
    if homo_match:
        homo_ev = float(homo_match.group(1)) * HARTREE_TO_EV
    if lumo_match:
        lumo_ev = float(lumo_match.group(1)) * HARTREE_TO_EV
    
    # If not explicitly printed, we parse the orbital list
    if homo_ev is None or lumo_ev is None:
        # Fallback: Parse orbital list
        # Find the block of orbital energies
        # This is fragile and depends on DFTB+ version. 
        # Let's try to find "Orbital energies" section.
        orbitals = []
        lines = content.split('\n')
        in_orbital_block = False
        for line in lines:
            if "Orbital energies" in line or "Eigenvalues" in line:
                in_orbital_block = True
                continue
            if in_orbital_block:
                if line.strip().startswith("Orbital") or line.strip().startswith("State"):
                    # New section or header
                    if "Orbital" in line and "energies" not in line:
                        in_orbital_block = False
                        continue
                if re.match(r"\s*\d+\s+[-+]?\d*\.\d+", line):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            energy_hartree = float(parts[1])
                            orbitals.append(energy_hartree)
                        except ValueError:
                            pass
                # End of block detection (empty line or new section)
                if not line.strip() and orbitals:
                    # Check if next line is a new header
                    # For simplicity, assume we collect until a non-matching line
                    pass
        
        if orbitals:
            # Sort to find HOMO/LUMO
            # We need the number of electrons.
            # This is complex without parsing the charge section.
            # Assume for now we just take the highest and second highest as HOMO/LUMO if we can't determine occupancy.
            # A safer bet for a generic parser is to look for the explicit HOMO/LUMO lines again.
            # If we can't find them, we might have to rely on the 'molecular_orbitals.bin'
            pass
    
    if homo_ev is None or lumo_ev is None:
        # Try to read from molecular_orbitals.bin if available
        mo_file = work_dir / "molecular_orbitals.bin"
        if mo_file.exists():
            # This is a binary file, parsing is complex.
            # We rely on the text output for now.
            logger.warning("Could not parse HOMO/LUMO from text output. molecular_orbitals.bin exists but is not parsed.")
            # Fallback: raise error if we still don't have it
            if homo_ev is None:
                raise ValueError("HOMO energy not found in DFTB+ output.")
            if lumo_ev is None:
                raise ValueError("LUMO energy not found in DFTB+ output.")
        else:
            if homo_ev is None:
                raise ValueError("HOMO energy not found in DFTB+ output.")
            if lumo_ev is None:
                raise ValueError("LUMO energy not found in DFTB+ output.")
    
    # Parse Mayer Bond Orders
    # DFTB+ writes bond orders to bondorder.bin or similar.
    # If WriteBonds = Yes, it might print in dftb_out.
    mayer_bonds = []
    # Look for "Mayer Bond Orders" in dftb_out
    # Example:
    # Mayer Bond Order Matrix:
    #    1    2    0.1234
    #    1    3    0.0000
    # ...
    bond_lines = re.findall(r"(\d+)\s+(\d+)\s+([-+]?\d*\.\d+|\d+)", content)
    # Filter for lines that look like bond orders (3 columns)
    # This regex is very generic. We need to ensure we are in the bond order section.
    # For now, we assume any 3-integer/float tuple found after "Mayer" or "Bond Order" is valid.
    # A more robust way is to parse the binary file if available.
    # Since the task asks for "Mayer bond orders", we try to extract them.
    
    # Let's assume the text output contains a matrix or list.
    # If the binary file 'bondorder.bin' is present, we could use a library to read it, 
    # but that adds complexity. We'll rely on text parsing for now.
    
    # Re-scan for "Mayer Bond Order" section
    in_bond_section = False
    bond_data = []
    for line in lines:
        if "Mayer Bond Order" in line or "Bond Order Matrix" in line:
            in_bond_section = True
            continue
        if in_bond_section:
            if not line.strip():
                in_bond_section = False
                continue
            parts = line.split()
            if len(parts) >= 3:
                try:
                    a1 = int(parts[0])
                    a2 = int(parts[1])
                    order = float(parts[2])
                    bond_data.append((a1, a2, order))
                except ValueError:
                    pass
    
    mayer_bonds = bond_data
    
    return {
        "homo_energy": homo_ev,
        "lumo_energy": lumo_ev,
        "mayer_bond_orders": mayer_bonds,
        "total_energy": total_energy_ev
    }


def calculate_descriptors_for_molecule(
    smiles: str,
    molecule_id: str,
    work_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main entry point to calculate descriptors for a single molecule.
    
    Args:
        smiles: SMILES string.
        molecule_id: Unique identifier for the molecule.
        work_dir: Optional working directory. If None, a temp directory is created.
        
    Returns:
        Dictionary with calculated descriptors and metadata.
        
    Raises:
        ConvergenceError: If geometry optimization fails.
        OOMError: If memory limit exceeded.
        RuntimeError: If DFTB+ execution fails.
    """
    # Create a unique working directory
    if work_dir is None:
        base_temp = Path(tempfile.mkdtemp(prefix=f"dftb_{molecule_id}_"))
    else:
        base_temp = Path(work_dir) / molecule_id
        base_temp.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Convert SMILES to XYZ
        xyz_path = base_temp / "input.xyz"
        smiles_to_xyz(smiles, xyz_path)
        
        # 2. Create DFTB+ input
        create_dftb_input(xyz_path, base_temp)
        
        # 3. Run DFTB+
        log_dftb_invocation(molecule_id, str(base_temp))
        run_dftb_work(base_temp)
        
        # 4. Parse output
        descriptors = parse_dftb_output(base_temp)
        
        # 5. Add metadata
        descriptors["molecule_id"] = molecule_id
        descriptors["smiles"] = smiles
        descriptors["status"] = "success"
        
        return descriptors
        
    except (ConvergenceError, OOMError):
        # Re-raise to be handled by the pipeline
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing {molecule_id}: {e}")
        raise RuntimeError(f"Failed to process {molecule_id}: {e}")
    finally:
        # Optional: Clean up temp directory if it was created here
        # For debugging, we might want to keep it. 
        # For now, we leave it to the caller or OS cleanup.
        pass


def main():
    """
    CLI entry point for testing the calculator on a single molecule.
    Usage: python -m code.dftb_calculator --smiles "CCO" --id "test_001"
    """
    import argparse
    parser = argparse.ArgumentParser(description="DFTB+ Calculator for single molecule")
    parser.add_argument("--smiles", type=str, required=True, help="SMILES string")
    parser.add_argument("--id", type=str, required=True, help="Molecule ID")
    parser.add_argument("--outdir", type=str, default=None, help="Output directory (default: temp)")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    out_dir = Path(args.outdir) if args.outdir else None
    try:
        result = calculate_descriptors_for_molecule(args.smiles, args.id, out_dir)
        print(f"Results for {args.id}:")
        print(f"  HOMO: {result['homo_energy']:.4f} eV")
        print(f"  LUMO: {result['lumo_energy']:.4f} eV")
        print(f"  Total Energy: {result['total_energy']:.4f} eV")
        print(f"  Mayer Bonds: {len(result['mayer_bond_orders'])}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()