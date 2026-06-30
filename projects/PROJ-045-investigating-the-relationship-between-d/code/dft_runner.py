import logging
import os
import signal
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pymatgen.core import Structure, Lattice

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SupercellExpansionError(Exception):
    """Raised when supercell expansion fails or constraints are violated."""
    pass

class JobTimeoutError(Exception):
    """Raised when a DFT job exceeds the time limit."""
    pass

def create_supercell(structure: Structure, scale: Tuple[int, int, int] = (2, 2, 2)) -> Structure:
    """
    Create a supercell by scaling the input structure.
    
    Args:
        structure: The base pymatgen Structure object.
        scale: Tuple of integers (a, b, c) for scaling factors.
        
    Returns:
        A new Structure object representing the supercell.
        
    Raises:
        SupercellExpansionError: If scaling fails or results in invalid structure.
    """
    try:
        supercell = structure * np.array(scale)
        if len(supercell) == 0:
            raise SupercellExpansionError("Supercell expansion resulted in zero atoms.")
        logger.info(f"Created supercell with {len(supercell)} atoms from scale {scale}")
        return supercell
    except Exception as e:
        raise SupercellExpansionError(f"Failed to create supercell: {str(e)}")

def get_high_fidelity_subset(compositions: List[Dict[str, Any]], max_count: int = 3) -> List[Dict[str, Any]]:
    """
    Select the high-fidelity subset for DFT calculations.
    
    Args:
        compositions: List of composition dictionaries.
        max_count: Maximum number of compositions to select.
        
    Returns:
        List of selected composition dictionaries.
    """
    # For now, select the first N compositions with complete data
    # In a real implementation, this would filter based on data completeness
    subset = []
    count = 0
    for comp in compositions:
        if count >= max_count:
            break
        # Check if composition has required data
        if comp.get('has_complete_data', False):
            subset.append(comp)
            count += 1
    logger.info(f"Selected {len(subset)} compositions for high-fidelity DFT subset")
    return subset

def generate_qe_input(structure: Structure, output_path: Path, job_id: str, 
                     cutoff: float = 50.0, k_mesh: Tuple[int, int, int] = (2, 2, 2)) -> Path:
    """
    Generate a Quantum ESPRESSO input file for a given structure.
    
    Args:
        structure: The pymatgen Structure object.
        output_path: Directory to save the input file.
        job_id: Unique identifier for the job.
        cutoff: Plane-wave cutoff energy in Ry.
        k_mesh: K-point mesh tuple.
        
    Returns:
        Path to the generated input file.
    """
    output_path.mkdir(parents=True, exist_ok=True)
    input_file = output_path / f"{job_id}.in"
    
    with open(input_file, 'w') as f:
        f.write("&CONTROL\n")
        f.write(f"    calculation = 'scf',\n")
        f.write(f"    prefix = '{job_id}',\n")
        f.write(f"    outdir = './tmp',\n")
        f.write(f"    pseudo_dir = './pseudo',\n")
        f.write("/\n")
        f.write("&SYSTEM\n")
        f.write(f"    ibrav = 0,\n")
        f.write(f"    nat = {len(structure)},\n")
        f.write(f"    ntyp = {len(set(site.species_string for site in structure))},\n")
        f.write(f"    ecutwfc = {cutoff},\n")
        f.write(f"    ecutrho = {4.0 * cutoff},\n")
        f.write("/\n")
        f.write("&ELECTRONS\n")
        f.write(f"    conv_thr = 1.0d-8,\n")
        f.write("/\n")
        f.write("ATOMIC_SPECIES\n")
        
        elements = sorted(set(site.species_string for site in structure))
        for elem in elements:
            # Placeholder for pseudopotential mass and file
            f.write(f"    {elem}  1.00  {elem}.UPF\n")
        
        f.write("ATOMIC_POSITIONS (crystal)\n")
        for site in structure:
            coords = site.frac_coords
            f.write(f"    {site.species_string} {coords[0]:.6f} {coords[1]:.6f} {coords[2]:.6f}\n")
        
        f.write("K_POINTS automatic\n")
        f.write(f"    {k_mesh[0]} {k_mesh[1]} {k_mesh[2]} 0 0 0\n")
    
    logger.info(f"Generated QE input file: {input_file}")
    return input_file

def simulate_dft_job(structure: Structure, job_id: str, output_dir: Path, 
                    timeout_seconds: int = 3600) -> Dict[str, Any]:
    """
    Simulate a DFT job execution with timeout detection and partial result preservation.
    
    This function mimics the execution of a DFT calculation, tracking progress and
    handling timeouts by saving partial results.
    
    Args:
        structure: The pymatgen Structure object.
        job_id: Unique identifier for the job.
        output_dir: Directory to save results.
        timeout_seconds: Maximum allowed execution time in seconds.
        
    Returns:
        Dictionary containing job results and status.
    """
    start_time = time.time()
    result = {
        'job_id': job_id,
        'status': 'running',
        'start_time': start_time,
        'atom_count': len(structure),
        'progress': 0.0,
        'energy': None,
        'force_max': None,
        'partial_data': {}
    }
    
    # Simulate job execution with checkpoints
    checkpoints = [0.2, 0.4, 0.6, 0.8, 1.0]
    total_steps = 100
    current_step = 0
    
    output_dir.mkdir(parents=True, exist_ok=True)
    partial_file = output_dir / f"{job_id}_partial.json"
    final_file = output_dir / f"{job_id}_result.json"
    
    try:
        for i in range(total_steps):
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                raise JobTimeoutError(f"Job {job_id} exceeded timeout of {timeout_seconds}s")
            
            current_step = i + 1
            progress = current_step / total_steps
            result['progress'] = progress
            
            # Simulate computation at checkpoints
            if progress in checkpoints or i == total_steps - 1:
                # Save partial results
                result['partial_data'] = {
                    'step': current_step,
                    'elapsed': elapsed,
                    'intermediate_energy': -10.0 * progress,  # Simulated value
                    'intermediate_max_force': 0.5 * (1 - progress)  # Simulated convergence
                }
                
                with open(partial_file, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                
                logger.info(f"Job {job_id} progress: {progress*100:.1f}% - Partial results saved")
            
            # Simulate work
            time.sleep(0.01)  # Small delay to simulate computation
        
        # Job completed successfully
        result['status'] = 'completed'
        result['end_time'] = time.time()
        result['elapsed'] = result['end_time'] - result['start_time']
        result['energy'] = -10.0  # Final simulated energy
        result['force_max'] = 0.01  # Final simulated max force
        
        # Save final result
        with open(final_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        # Clean up partial file if completed successfully
        if partial_file.exists():
            partial_file.unlink()
        
        logger.info(f"Job {job_id} completed successfully in {result['elapsed']:.2f}s")
        
    except JobTimeoutError as e:
        logger.warning(f"Job {job_id} timed out: {str(e)}")
        result['status'] = 'timeout'
        result['end_time'] = time.time()
        result['elapsed'] = result['end_time'] - result['start_time']
        
        # Ensure partial results are saved
        with open(partial_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"Partial results for {job_id} preserved at {partial_file}")
        raise
        
    except Exception as e:
        logger.error(f"Job {job_id} failed with error: {str(e)}")
        result['status'] = 'failed'
        result['end_time'] = time.time()
        result['elapsed'] = result['end_time'] - result['start_time']
        result['error'] = str(e)
        
        # Save partial results for failed jobs too
        with open(partial_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        raise
    
    return result

def process_high_fidelity_subset(compositions: List[Dict[str, Any]], output_dir: Path, 
                                 timeout_seconds: int = 3600) -> List[Dict[str, Any]]:
    """
    Process the high-fidelity subset of compositions with DFT calculations.
    
    Args:
        compositions: List of composition dictionaries for high-fidelity subset.
        output_dir: Directory to save results.
        timeout_seconds: Maximum allowed execution time per job.
        
    Returns:
        List of result dictionaries for each composition.
    """
    results = []
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, comp in enumerate(compositions):
        job_id = f"dft_job_{comp.get('mp_id', f'unknown_{i}')}"
        logger.info(f"Processing high-fidelity job {i+1}/{len(compositions)}: {job_id}")
        
        try:
            # Create structure (simulated)
            structure = Structure.from_spacegroup(
                225,  # Fm-3m
                Lattice.cubic(4.0),
                [{"species": ["Li", "O"], "coords": [[0, 0, 0], [0.25, 0.25, 0.25]]}]
            )
            
            # Generate QE input
            generate_qe_input(structure, output_dir / job_id, job_id)
            
            # Run simulation with timeout handling
            result = simulate_dft_job(structure, job_id, output_dir, timeout_seconds)
            results.append(result)
            
        except JobTimeoutError:
            # Timeout already handled in simulate_dft_job
            logger.warning(f"Skipping further processing for timed out job: {job_id}")
            # Result already saved as partial
            continue
        except Exception as e:
            logger.error(f"Failed to process {job_id}: {str(e)}")
            results.append({
                'job_id': job_id,
                'status': 'failed',
                'error': str(e)
            })
    
    logger.info(f"Processed {len(results)} high-fidelity jobs")
    return results

def main():
    """Main entry point for DFT runner with timeout handling."""
    logger.info("Starting DFT runner with timeout detection and partial result preservation")
    
    # Example usage
    test_compositions = [
        {'mp_id': 'mp-1234', 'has_complete_data': True},
        {'mp_id': 'mp-5678', 'has_complete_data': True},
        {'mp_id': 'mp-9012', 'has_complete_data': True}
    ]
    
    high_fidelity = get_high_fidelity_subset(test_compositions, max_count=3)
    
    output_dir = Path("data/processed/dft_results")
    
    try:
        results = process_high_fidelity_subset(high_fidelity, output_dir, timeout_seconds=60)
        
        # Summary
        completed = sum(1 for r in results if r.get('status') == 'completed')
        timed_out = sum(1 for r in results if r.get('status') == 'timeout')
        failed = sum(1 for r in results if r.get('status') == 'failed')
        
        logger.info(f"Summary: {completed} completed, {timed_out} timed out, {failed} failed")
        
        # Save summary
        summary = {
            'total_jobs': len(results),
            'completed': completed,
            'timed_out': timed_out,
            'failed': failed,
            'results': results
        }
        
        summary_file = output_dir / "dft_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Summary saved to {summary_file}")
        
    except Exception as e:
        logger.error(f"Fatal error in DFT runner: {str(e)}")
        raise

if __name__ == "__main__":
    main()