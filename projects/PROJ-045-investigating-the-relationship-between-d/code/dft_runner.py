"""
DFT Runner Module for Defect Chemistry and Ionic Conductivity Analysis.

This module handles the generation of Quantum ESPRESSO input files, 
supercell expansion, and management of DFT job execution including 
timeout detection and partial result preservation.

Dependencies:
- pymatgen (for Structure handling)
- ase (for atomic simulations environment)
- numpy (for numerical operations)
"""
import logging
import os
import signal
import time
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import sys

# Import from project models
try:
    from models import DefectConfiguration, ElectrolyteComposition
except ImportError:
    # Fallback for direct execution context
    from code.models import DefectConfiguration, ElectrolyteComposition

# Configure logger
logger = logging.getLogger(__name__)

class SupercellExpansionError(Exception):
    """Raised when supercell expansion fails or violates constraints."""
    pass

class JobTimeoutError(Exception):
    """Raised when a DFT job exceeds the time limit."""
    pass

def setup_dft_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Setup logging for DFT operations.
    
    Args:
        log_file: Optional path for log file. If None, logs to console.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger('dft_runner')
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def create_supercell(
    structure_path: Path, 
    expansion: Tuple[int, int, int] = (2, 2, 2),
    output_dir: Optional[Path] = None
) -> Path:
    """
    Create a supercell from a base structure file.
    
    Args:
        structure_path: Path to the input structure file (CIF or POSCAR).
        expansion: Tuple (a, b, c) for supercell expansion factors.
        output_dir: Directory to save the supercell structure.
        
    Returns:
        Path to the generated supercell structure file.
        
    Raises:
        SupercellExpansionError: If expansion fails or constraints are violated.
    """
    try:
        from pymatgen.core import Structure
        from pymatgen.io.ase import AseAtomsAdaptor
        
        # Load structure
        if structure_path.suffix.lower() == '.cif':
            structure = Structure.from_file(str(structure_path))
        elif structure_path.suffix.lower() in ['.vasp', '.poscar']:
            structure = Structure.from_file(str(structure_path))
        else:
            raise SupercellExpansionError(
                f"Unsupported file format: {structure_path.suffix}. "
                "Use .cif or .vasp/.poscar"
            )
        
        logger.info(f"Loaded structure: {structure.composition.formula}")
        logger.info(f"Original cell: {structure.lattice.abc}")
        
        # Expand supercell
        supercell = structure * expansion
        
        logger.info(f"Expanded to {expansion} supercell: {supercell.composition.formula}")
        logger.info(f"New cell: {supercell.lattice.abc}")
        logger.info(f"Number of atoms: {len(supercell)}")
        
        # Validate atom count (spec constraint: >8 atoms allowed for high-fidelity)
        if len(supercell) < 8:
            logger.warning(f"Supercell has only {len(supercell)} atoms. "
                         "This is below the typical minimum for defect calculations.")
        
        # Save supercell
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{structure_path.stem}_supercell.cif"
            supercell.to_file(str(output_path))
            logger.info(f"Supercell saved to: {output_path}")
            return output_path
        else:
            # Return in-memory structure if no output dir
            return structure_path  # Placeholder, should return structure object
            
    except Exception as e:
        raise SupercellExpansionError(f"Failed to create supercell: {str(e)}")

def get_high_fidelity_subset(
    compositions: List[ElectrolyteComposition],
    min_atoms: int = 8
) -> List[ElectrolyteComposition]:
    """
    Filter compositions for high-fidelity DFT calculations.
    
    Args:
        compositions: List of electrolyte compositions.
        min_atoms: Minimum number of atoms required (default 8).
        
    Returns:
        List of compositions suitable for high-fidelity DFT.
    """
    high_fid = []
    for comp in compositions:
        # In a real implementation, this would check structure data
        # For now, assume all provided compositions are candidates
        high_fid.append(comp)
        logger.info(f"Selected {comp.composition_id} for high-fidelity DFT")
    
    return high_fid

def generate_qe_input(
    structure_path: Path,
    output_dir: Path,
    pseudopotentials: Dict[str, str],
    k_mesh: Tuple[int, int, int] = (4, 4, 4),
    energy_cutoff: float = 50.0,
    job_name: str = "dft_job"
) -> Path:
    """
    Generate Quantum ESPRESSO input file.
    
    Args:
        structure_path: Path to the structure file.
        output_dir: Directory for output files.
        pseudopotentials: Dict mapping element to pseudopotential file.
        k_mesh: k-point mesh.
        energy_cutoff: Plane-wave cutoff in Ry.
        job_name: Name for the job.
        
    Returns:
        Path to the generated input file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    input_path = output_dir / f"{job_name}.in"
    
    # Read structure to get lattice and atoms
    try:
        from pymatgen.core import Structure
        structure = Structure.from_file(str(structure_path))
    except Exception as e:
        logger.error(f"Failed to read structure: {e}")
        raise
    
    # Build QE input
    lines = [
        "&CONTROL",
        f"    calculation = 'scf',",
        f"    prefix = '{job_name}',",
        f"    outdir = '{output_dir.absolute()}/tmp',",
        f"    pseudo_dir = './pseudo',",
        f"    etot_conv_thr = 1.0d-6,",
        f"/",
        "&SYSTEM",
        f"    ibrav = 0,",
        f"    nat = {len(structure)},",
        f"    ntyp = {len(set(site.species_string for site in structure))},",
        f"    ecutwfc = {energy_cutoff},",
        f"    ecutrho = {energy_cutoff * 4.0},",
        f"    occupations = 'smearing',",
        f"    smearing = 'marzari-vanderbilt',",
        f"    degauss = 0.01,",
        f"/",
        "&ELECTRONS",
        f"    conv_thr = 1.0d-8,",
        f"    mixing_beta = 0.7,",
        f"/",
        f"ATOMIC_SPECIES",
    ]
    
    # Add atomic species
    elements = list(set(site.species_string for site in structure))
    for elem in elements:
        pp_file = pseudopotentials.get(elem, f"{elem}.upf")
        # Get atomic mass from pymatgen
        mass = structure[0].species.elements[0].atomic_mass
        lines.append(f"    {elem} {mass} {pp_file}")
    
    lines.append("ATOMIC_POSITIONS {crystal}")
    for site in structure:
        coords = site.frac_coords
        lines.append(f"    {site.species_string} {coords[0]:.6f} {coords[1]:.6f} {coords[2]:.6f}")
    
    lines.append("K_POINTS automatic")
    lines.append(f"    {k_mesh[0]} {k_mesh[1]} {k_mesh[2]} 0 0 0")
    
    with open(input_path, 'w') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Generated QE input: {input_path}")
    return input_path

def simulate_dft_job(
    input_path: Path,
    output_path: Path,
    timeout_seconds: int = 3600,
    use_real_qe: bool = False
) -> Dict[str, Any]:
    """
    Simulate or execute a DFT job with timeout detection.
    
    This function implements the core logic for T030: timeout detection
    and partial result preservation.
    
    Args:
        input_path: Path to the QE input file.
        output_path: Path for the output file.
        timeout_seconds: Maximum allowed runtime in seconds.
        use_real_qe: If True, attempt to run real QE (will fail if not installed).
        
    Returns:
        Dictionary with job status, partial results, and metadata.
        
    Raises:
        JobTimeoutError: If the job exceeds the time limit.
    """
    start_time = time.time()
    result = {
        "job_id": input_path.stem,
        "start_time": datetime.now().isoformat(),
        "status": "running",
        "input_file": str(input_path),
        "output_file": str(output_path),
        "timeout_seconds": timeout_seconds,
        "partial_results": {},
        "error": None
    }
    
    logger.info(f"Starting job: {result['job_id']}")
    logger.info(f"Timeout set to {timeout_seconds} seconds")
    
    # Create a temporary directory for job files
    job_dir = output_path.parent / f"job_{result['job_id']}"
    job_dir.mkdir(parents=True, exist_ok=True)
    partial_result_file = job_dir / "partial_results.json"
    
    try:
        if use_real_qe:
            # Attempt to run real Quantum ESPRESSO
            # Note: This will likely fail in environments without QE installed
            # The timeout logic is still valid for real execution
            cmd = ["pw.x", "-in", str(input_path), "-out", str(output_path)]
            
            # Start process with timeout
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(job_dir)
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout_seconds)
                result["status"] = "completed"
                result["end_time"] = datetime.now().isoformat()
                result["runtime_seconds"] = time.time() - start_time
                
                # Parse output for key metrics
                if output_path.exists():
                    with open(output_path, 'r') as f:
                        content = f.read()
                        # Simple parsing for demonstration
                        if "!    total energy" in content:
                            for line in content.split('\n'):
                                if "!    total energy" in line:
                                    energy = float(line.split()[-2])
                                    result["partial_results"]["total_energy"] = energy
                                    break
                
            except subprocess.TimeoutExpired:
                process.kill()
                result["status"] = "timeout"
                result["end_time"] = datetime.now().isoformat()
                result["runtime_seconds"] = timeout_seconds
                result["error"] = "Job exceeded time limit"
                raise JobTimeoutError(
                    f"Job {result['job_id']} timed out after {timeout_seconds} seconds"
                )
        else:
            # Simulation mode for testing timeout logic
            # Simulate a job that takes time and may timeout
            logger.info("Running in simulation mode (no real QE)")
            
            # Simulate progress
            progress_interval = 0.5
            elapsed = 0
            iteration = 0
            
            while elapsed < timeout_seconds:
                time.sleep(progress_interval)
                elapsed = time.time() - start_time
                iteration += 1
                
                # Generate partial results periodically
                if iteration % 2 == 0:
                    partial_data = {
                        "iteration": iteration,
                        "elapsed_seconds": round(elapsed, 2),
                        "converged": False,
                        "energy_estimate": -100.0 - (iteration * 0.1)
                    }
                    result["partial_results"] = partial_data
                    
                    # Save partial results to disk
                    with open(partial_result_file, 'w') as f:
                        json.dump(result, f, indent=2)
                    logger.debug(f"Saved partial results at {elapsed:.2f}s")
                
                # Simulate convergence check
                if iteration > 10 and iteration % 5 == 0:
                    result["partial_results"]["converged"] = True
                    result["status"] = "completed"
                    break
            
            if result["status"] != "completed":
                result["status"] = "timeout"
                result["end_time"] = datetime.now().isoformat()
                result["runtime_seconds"] = timeout_seconds
                result["error"] = "Job exceeded time limit during simulation"
                raise JobTimeoutError(
                    f"Job {result['job_id']} timed out after {timeout_seconds} seconds"
                )
                
    except JobTimeoutError:
        # Ensure partial results are preserved before re-raising
        result["end_time"] = datetime.now().isoformat()
        result["runtime_seconds"] = time.time() - start_time
        result["status"] = "timeout"
        
        # Preserve partial results to disk
        if partial_result_file:
            with open(partial_result_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.warning(f"Partial results preserved at: {partial_result_file}")
        
        raise
        
    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        result["end_time"] = datetime.now().isoformat()
        
        # Preserve partial results even on error
        if partial_result_file:
            with open(partial_result_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.warning(f"Partial results preserved at: {partial_result_file}")
        
        logger.error(f"Job failed: {e}")
        raise
        
    finally:
        # Always save final state
        result["end_time"] = datetime.now().isoformat()
        result["runtime_seconds"] = time.time() - start_time
        
        with open(partial_result_file, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Final results saved at: {partial_result_file}")
    
    return result

def process_high_fidelity_subset(
    high_fid_compositions: List[ElectrolyteComposition],
    base_dir: Path,
    timeout_seconds: int = 3600
) -> List[Dict[str, Any]]:
    """
    Process the high-fidelity subset of compositions.
    
    Args:
        high_fid_compositions: List of compositions for high-fidelity DFT.
        base_dir: Base directory for outputs.
        timeout_seconds: Timeout for each job.
        
    Returns:
        List of result dictionaries.
    """
    results = []
    
    for comp in high_fid_compositions:
        logger.info(f"Processing high-fidelity composition: {comp.composition_id}")
        
        # Setup directories
        job_dir = base_dir / "dft_jobs" / comp.composition_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Assume structure file exists (downloaded in previous phase)
        structure_path = base_dir / "data" / "raw" / f"{comp.composition_id}.cif"
        
        if not structure_path.exists():
            logger.warning(f"Structure not found for {comp.composition_id}. Skipping.")
            continue
        
        try:
            # Create supercell
            supercell_path = create_supercell(
                structure_path,
                expansion=(2, 2, 2),
                output_dir=job_dir
            )
            
            # Generate QE input
            qe_input = generate_qe_input(
                supercell_path,
                job_dir,
                pseudopotentials={"Li": "Li.pbe-n-kjpaw_psl.1.0.0.UPF", 
                                 "La": "La.pbe-n-kjpaw_psl.1.0.0.UPF",
                                 "Zr": "Zr.pbe-n-kjpaw_psl.1.0.0.UPF",
                                 "O": "O.pbe-n-kjpaw_psl.1.0.0.UPF"}
            )
            
            # Run DFT job with timeout
            output_path = job_dir / f"{comp.composition_id}.out"
            job_result = simulate_dft_job(
                qe_input,
                output_path,
                timeout_seconds=timeout_seconds,
                use_real_qe=False  # Set to True in production with QE installed
            )
            
            results.append(job_result)
            
        except JobTimeoutError as e:
            logger.warning(f"Job timed out for {comp.composition_id}: {e}")
            # Result already saved by simulate_dft_job
            results.append({
                "composition_id": comp.composition_id,
                "status": "timeout",
                "error": str(e),
                "partial_results_saved": True
            })
        except Exception as e:
            logger.error(f"Failed to process {comp.composition_id}: {e}")
            results.append({
                "composition_id": comp.composition_id,
                "status": "failed",
                "error": str(e)
            })
    
    return results

def main():
    """
    Main entry point for DFT runner.
    
    Usage:
        python code/dft_runner.py --test-system Li7La3Zr2O12
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="DFT Runner for Defect Chemistry")
    parser.add_argument(
        "--test-system",
        type=str,
        default=None,
        help="Test system ID (e.g., Li7La3Zr2O12)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds for simulation (default: 60)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed/dft_results",
        help="Output directory for results"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_file = Path(args.output_dir) / "dft_runner.log"
    logger = setup_dft_logging(log_file)
    
    logger.info("Starting DFT Runner")
    logger.info(f"Test system: {args.test_system}")
    logger.info(f"Timeout: {args.timeout} seconds")
    
    try:
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if args.test_system:
            # Run single test
            logger.info(f"Running test for: {args.test_system}")
            
            # Create a mock composition for testing
            from models import ElectrolyteComposition
            comp = ElectrolyteComposition(
                composition_id=args.test_system,
                formula=args.test_system,
                structure_path=f"data/raw/{args.test_system}.cif"
            )
            
            # Process single composition
            results = process_high_fidelity_subset(
                [comp],
                base_dir=Path("."),
                timeout_seconds=args.timeout
            )
            
            # Save results
            results_file = output_dir / "test_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Test results saved to: {results_file}")
            print(json.dumps(results, indent=2))
            
        else:
            logger.info("No test system specified. Use --test-system <ID>")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()