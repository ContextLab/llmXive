import os
import time
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from logger import get_logger, info, error, warning, critical
from config import get_config, set_random_seed

def run_psi4_single(
    xyz_file: Path,
    output_file: Path,
    method: str = "b3lyp",
    basis: str = "def2-tzvp",
    damping: str = "bj",
    cp: bool = True,
    max_retries: int = 3,
) -> bool:
    """
    Run a single Psi4 calculation.

    Args:
        xyz_file: Path to the input XYZ file.
        output_file: Path for the Psi4 output file.
        method: DFT method (default: b3lyp).
        basis: Basis set (default: def2-tzvp).
        damping: Damping function for D3 (default: bj).
        cp: Whether to apply Counterpoise correction (default: True).
        max_retries: Maximum number of retry attempts (default: 3).

    Returns:
        True if successful, False otherwise.
    """
    logger = get_logger(__name__)
    config = get_config()
    set_random_seed(config.seed)

    psi4_input = f"""memory 2 GB
set {{
    basis {basis}
    dft_functional {method}
    dft_spherical_points 434
    dft_radial_points 99
    dft_grid_level 0
}}

# D3 dispersion correction
set {{
    dft_d3 true
    dft_d3_version 2
    dft_d3_s8 1.0
    dft_d3_sr 1.0
    dft_d3_beta6 0.0
    dft_d3_damping {damping}
}}

# Counterpoise correction
set {{
    bsse_type {'cp' if cp else 'none'}
}}

molecule {{
    read "{xyz_file}"
}}

energy('{method}/{basis}')
"""

    psi4_input_file = output_file.with_suffix(".inp")
    with open(psi4_input_file, "w") as f:
        f.write(psi4_input)

    logger.info(f"Running Psi4 calculation for {xyz_file}")

    for attempt in range(1, max_retries + 1):
        logger.info(f"Attempt {attempt}/{max_retries} for {xyz_file}")
        try:
            # Run psi4
            cmd = [
                "psi4",
                str(psi4_input_file),
                str(output_file),
            ]
            result = subprocess.run(
                cmd,
                cwd=output_file.parent,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
            )

            if result.returncode == 0:
                logger.info(f"Psi4 calculation succeeded for {xyz_file}")
                return True
            else:
                logger.warning(f"Psi4 failed for {xyz_file} (attempt {attempt}): {result.stderr}")
                if attempt == max_retries:
                    error(f"Psi4 failed after {max_retries} attempts for {xyz_file}")
                    return False
                time.sleep(5 * attempt)  # Exponential backoff

        except subprocess.TimeoutExpired:
            warning(f"Psi4 timed out for {xyz_file} (attempt {attempt})")
            if attempt == max_retries:
                error(f"Psi4 timed out after {max_retries} attempts for {xyz_file}")
                return False
            time.sleep(5 * attempt)
        except FileNotFoundError:
            error("Psi4 executable not found. Please ensure psi4 is installed and in PATH.")
            return False
        except Exception as e:
            error(f"Unexpected error running Psi4 for {xyz_file}: {e}")
            return False

    return False

def run_psi4_batch(
    xyz_files: List[Path],
    output_dir: Path,
    method: str = "b3lyp",
    basis: str = "def2-tzvp",
    damping: str = "bj",
    cp: bool = True,
    max_retries: int = 3,
) -> Dict[str, bool]:
    """
    Run a batch of Psi4 calculations.

    Args:
        xyz_files: List of paths to input XYZ files.
        output_dir: Directory for output files.
        method: DFT method.
        basis: Basis set.
        damping: Damping function for D3.
        cp: Whether to apply Counterpoise correction.
        max_retries: Maximum number of retry attempts.

    Returns:
        Dictionary mapping input file names to success status.
    """
    logger = get_logger(__name__)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    for xyz_file in xyz_files:
        output_file = output_dir / f"{xyz_file.stem}.out"
        success = run_psi4_single(
            xyz_file,
            output_file,
            method=method,
            basis=basis,
            damping=damping,
            cp=cp,
            max_retries=max_retries,
        )
        results[xyz_file.name] = success

    return results

def main() -> None:
    """Main entry point for running Psi4 calculations."""
    logger = get_logger(__name__)
    config = get_config()
    set_random_seed(config.seed)

    # Example usage:
    # xyz_files = [Path("data/raw/ion_pair_1.xyz"), Path("data/raw/ion_pair_2.xyz")]
    # output_dir = Path("data/derived/psi4_outputs")
    # results = run_psi4_batch(xyz_files, output_dir)
    # logger.info(f"Batch results: {results}")

    logger.info("Psi4 runner ready. Call run_psi4_batch() with your files.")

if __name__ == "__main__":
    main()