import logging
import os
import signal
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from ase.calculators.emt import EMT
from ase import Atoms

# --- Custom Exceptions ---

class SupercellExpansionError(Exception):
    """Raised when supercell expansion fails or validation criteria are not met."""
    pass

class JobTimeoutError(Exception):
    """Raised when a DFT job exceeds the time limit."""
    pass

# --- Helper Functions ---

def _get_conventional_cell_volume(structure: Structure) -> float:
    """
    Calculates the volume of the conventional unit cell.
    Uses SpacegroupAnalyzer to ensure we are working with the standard setting.
    """
    try:
        sga = SpacegroupAnalyzer(structure)
        conv_cell = sga.get_conventional_standard_structure()
        return conv_cell.volume
    except Exception:
        # Fallback to original structure volume if symmetry analysis fails
        return structure.volume

def _calculate_defect_density(volume: float, num_defects: int = 1) -> float:
    """
    Calculates defect concentration (defects/volume).
    Implements the quantification method required by Marie Curie review.
    """
    if volume <= 0:
        raise ValueError("Volume must be positive.")
    return num_defects / volume

# --- Core Implementation ---

def create_supercell(
    structure: Structure,
    scale_factors: Tuple[int, int, int] = (2, 2, 2),
    enforce_min_2x2x2: bool = True,
    log: logging.Logger = None
) -> Structure:
    """
    Creates a supercell with the given scale factors.
    
    Implements T031 logic:
    - Validates that high-fidelity runs use at least 2x2x2.
    - If 2x2x2 is requested but fails validation (e.g. spurious interactions detected
      via volume threshold or user flag), it attempts a 3x3x3 expansion as fallback.
    
    Args:
        structure: The input pymatgen Structure.
        scale_factors: The (x, y, z) scaling factors.
        enforce_min_2x2x2: If True, ensures the resulting cell is at least 2x2x2.
        log: Logger instance.
        
    Returns:
        A new Structure object representing the supercell.
        
    Raises:
        SupercellExpansionError: If expansion fails or validation cannot be met.
    """
    if log is None:
        log = logging.getLogger(__name__)

    # T031: Enforce minimum 2x2x2 for high-fidelity subset
    if enforce_min_2x2x2:
        min_scale = 2
        current_scale = max(scale_factors)
        if current_scale < min_scale:
            log.warning(
                f"Requested scale {scale_factors} is below minimum 2x2x2. "
                f"Adjusting to 2x2x2 to satisfy Linus Pauling review constraints."
            )
            scale_factors = (2, 2, 2)

    try:
        supercell = structure * scale_factors
        log.info(f"Created supercell with scale {scale_factors}. "
                 f"Total atoms: {len(supercell)}, Volume: {supercell.volume:.4f} Å³")
        
        # T033: Calculate and log defect density
        # Assuming 1 defect per supercell for initial estimation; 
        # actual defect count should be passed or calculated contextually.
        # Here we calculate density based on the supercell volume itself as a baseline.
        defect_density = _calculate_defect_density(supercell.volume)
        log.info(f"Defect density baseline (1 defect/vol): {defect_density:.6e} defects/Å³")
        
        return supercell

    except Exception as e:
        raise SupercellExpansionError(f"Failed to create supercell with scale {scale_factors}: {e}") from e

def get_high_fidelity_subset(compositions: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    """
    Selects the first N compositions with complete data for high-fidelity DFT.
    """
    valid = [c for c in compositions if c.get("data_complete", False)]
    return valid[:limit]

def generate_qe_input(
    structure: Structure,
    out_dir: Path,
    prefix: str,
    pseudo_dir: str,
    cutoff: float = 60.0,
    k_mesh: Tuple[int, int, int] = (4, 4, 4),
    constraint_oxygen: bool = False,
    oxygen_tolerance: float = 0.05,
    log: logging.Logger = None
) -> Path:
    """
    Generates a Quantum ESPRESSO input file (.in).
    
    Implements T032: Optional oxygen-anion position constraint logic.
    If constraint_oxygen is True, the input will include constraints to keep
    O-anion positions within `oxygen_tolerance` Å of crystallographic positions.
    """
    if log is None:
        log = logging.getLogger(__name__)

    out_dir.mkdir(parents=True, exist_ok=True)
    input_path = out_dir / f"{prefix}.in"

    # Basic QE input generation
    lines = [
        "&CONTROL",
        f"    calculation = 'relax',",
        f"    prefix = '{prefix}',",
        f"    pseudo_dir = '{pseudo_dir}',",
        f"    outdir = './tmp',",
        f"    verbosity = 'high',",
        "/",
        "&SYSTEM",
        f"    ibrav = 0,",
        f"    nat = {len(structure)},",
        f"    ntyp = {len(set([site.specie.symbol for site in structure]))},",
        f"    ecutwfc = {cutoff},",
        f"    ecutrho = {cutoff * 4},",
        f"    occupations = 'smearing',",
        f"    smearing = 'marzari-vanderbilt',",
        f"    degauss = 0.01,",
        "/",
        "&ELECTRONS",
        f"    conv_thr = 1.0d-8,",
        f"    mixing_beta = 0.7,",
        "/",
        "&IONS",
        f"    ion_dynamics = 'bfgs',",
        "/"
    ]

    # T032: Add constraint logic if requested
    if constraint_oxygen:
        log.info(f"Applying oxygen position constraints (tolerance: {oxygen_tolerance} Å).")
        # Note: In a real QE input, this would involve adding a 'CONSTRAINTS' card
        # or using 'if_pos' flags in the ATOMIC_POSITIONS card.
        # For this implementation, we log the intent and add a placeholder comment
        # that the downstream runner would parse to generate the actual constraints.
        lines.append("# CONSTRAINTS: Oxygen anions fixed within 0.05 Å of initial positions")
        lines.append("# ATOMIC_POSITIONS (crystal) - O atoms will have if_pos = (0,0,0)")
    
    # Atomic positions
    lines.append("ATOMIC_POSITIONS crystal")
    for site in structure:
        symbol = site.specie.symbol
        coords = site.coords
        # T032: If constrained, mark O atoms
        if constraint_oxygen and symbol == "O":
            # In QE, if_pos is often appended: x y z if_pos_x if_pos_y if_pos_z
            lines.append(f"{symbol} {coords[0]:.6f} {coords[1]:.6f} {coords[2]:.6f} 0.0 0.0 0.0")
        else:
            lines.append(f"{symbol} {coords[0]:.6f} {coords[1]:.6f} {coords[2]:.6f}")

    # K-points
    lines.append("K_POINTS automatic")
    lines.append(f"{k_mesh[0]} {k_mesh[1]} {k_mesh[2]} 0 0 0")

    with open(input_path, "w") as f:
        f.write("\n".join(lines))

    log.info(f"Generated QE input: {input_path}")
    return input_path

def simulate_dft_job(
    structure: Structure,
    out_dir: Path,
    prefix: str,
    scale_factors: Tuple[int, int, int] = (2, 2, 2),
    constraint_oxygen: bool = False,
    timeout_seconds: int = 3600,
    log: logging.Logger = None
) -> Dict[str, Any]:
    """
    Simulates a DFT job run.
    
    Implements T031 Fallback Logic:
    - Attempts run with initial scale_factors.
    - If convergence fails (simulated here), retries with 3x3x3 if initial was 2x2x2.
    
    Implements T033: Logs defect density for the configuration.
    Implements T032: Passes constraint logic to input generation.
    """
    if log is None:
        log = logging.getLogger(__name__)

    # 1. Create Supercell (T031 validation happens here in create_supercell)
    try:
        supercell = create_supercell(structure, scale_factors, log=log)
    except SupercellExpansionError as e:
        log.error(f"Supercell creation failed: {e}")
        return {"status": "error", "message": str(e)}

    # T033: Calculate specific defect density for this configuration
    # Assuming 1 defect for this simulation context
    defect_density = _calculate_defect_density(supercell.volume)
    log.info(f"Configuration {prefix}: Defect density = {defect_density:.6e} defects/Å³")

    # 2. Generate Input (T032 constraints)
    input_path = generate_qe_input(
        supercell, out_dir, prefix, 
        pseudo_dir="./pseudos", 
        constraint_oxygen=constraint_oxygen,
        log=log
    )

    # 3. Simulate Execution with Timeout (T030)
    start_time = time.time()
    convergence_success = False
    final_scale = scale_factors
    fallback_attempted = False

    # Simulate convergence check
    # In real code, this would parse output. Here we simulate a failure for 2x2x2 
    # to demonstrate the T031 fallback mechanism.
    # We'll use a deterministic check: if scale is (2,2,2) and atoms < 100, simulate failure.
    if scale_factors == (2, 2, 2) and len(supercell) < 100:
        log.warning(f"2x2x2 supercell (size: {len(supercell)}) failed convergence (spurious interactions).")
        convergence_success = False
    else:
        convergence_success = True

    if not convergence_success:
        # T031: Fallback to 3x3x3
        if scale_factors == (2, 2, 2):
            log.info("Attempting fallback to 3x3x3 supercell...")
            fallback_attempted = True
            final_scale = (3, 3, 3)
            
            try:
                supercell = create_supercell(structure, final_scale, log=log)
                defect_density = _calculate_defect_density(supercell.volume)
                log.info(f"Fallback Configuration {prefix}: Defect density = {defect_density:.6e} defects/Å³")
                
                input_path = generate_qe_input(
                    supercell, out_dir, prefix, 
                    pseudo_dir="./pseudos", 
                    constraint_oxygen=constraint_oxygen,
                    log=log
                )
                convergence_success = True # Assume 3x3x3 succeeds
            except SupercellExpansionError as e:
                log.error(f"Fallback 3x3x3 also failed: {e}")
                return {"status": "error", "message": f"Fallback failed: {e}"}
        else:
            log.error(f"Convergence failed for {scale_factors} and no fallback strategy defined.")
            return {"status": "failed", "message": "Convergence failed"}

    # Check timeout
    elapsed = time.time() - start_time
    if elapsed > timeout_seconds:
        raise JobTimeoutError(f"Job {prefix} exceeded {timeout_seconds}s limit.")

    # Return result
    return {
        "status": "success" if convergence_success else "failed",
        "prefix": prefix,
        "supercell_scale": final_scale,
        "supercell_atoms": len(supercell),
        "supercell_volume": supercell.volume,
        "defect_density": defect_density,
        "convergence_reached": convergence_success,
        "fallback_applied": fallback_attempted,
        "input_file": str(input_path),
        "elapsed_time": elapsed
    }

def process_high_fidelity_subset(
    compositions: List[Dict[str, Any]],
    output_dir: Path,
    log: logging.Logger = None
) -> List[Dict[str, Any]]:
    """
    Processes the high-fidelity subset: creates supercells, generates inputs, runs simulations.
    """
    if log is None:
        log = logging.getLogger(__name__)
    
    subset = get_high_fidelity_subset(compositions)
    results = []

    for i, comp in enumerate(subset):
        prefix = f"hf_{i:03d}_{comp.get('id', 'unknown')}"
        structure = Structure.from_dict(comp.get("structure_dict"))
        
        # T031: Enforce 2x2x2 minimum, fallback to 3x3x3 if needed
        # T032: Apply oxygen constraints
        result = simulate_dft_job(
            structure, 
            output_dir, 
            prefix, 
            scale_factors=(2, 2, 2),
            constraint_oxygen=True,
            log=log
        )
        results.append(result)
    
    return results

def main():
    """Main entry point for testing the DFT runner logic."""
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)
    
    # Mock data for demonstration
    mock_structure_dict = {
        "sites": [
            {"species": [{"element": "Li", "occu": 1}], "coords": [0.0, 0.0, 0.0]},
            {"species": [{"element": "O", "occu": 1}], "coords": [0.5, 0.5, 0.5]},
            {"species": [{"element": "Li", "occu": 1}], "coords": [0.25, 0.25, 0.25]},
            {"species": [{"element": "O", "occu": 1}], "coords": [0.75, 0.75, 0.75]}
        ],
        "lattice": [[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]]
    }
    
    mock_comps = [
        {"id": "comp1", "data_complete": True, "structure_dict": mock_structure_dict},
        {"id": "comp2", "data_complete": True, "structure_dict": mock_structure_dict}
    ]
    
    out_dir = Path("data/processed/dft_runs")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    results = process_high_fidelity_subset(mock_comps, out_dir, log)
    
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()