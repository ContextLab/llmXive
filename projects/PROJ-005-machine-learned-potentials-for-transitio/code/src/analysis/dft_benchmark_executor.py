"""
DFT Benchmark Executor for T036b.

Executes a single DFT calculation using PSI4 on the median barrier sample
from the processed graphs dataset.
"""
import json
import logging
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import psi4

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.src.utils.config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


def get_cache_path() -> Path:
    """Return the path to the DFT benchmark cache file."""
    return get_project_root() / "code" / "data" / "results" / "dft_benchmark_cache.json"


def get_scarcity_flag_path() -> Path:
    """Return the path to the data scarcity flag file."""
    return get_project_root() / "code" / "data" / "processed" / "data_scarcity_flag.json"


def get_processed_graphs_path() -> Path:
    """Return the path to the processed graphs parquet file."""
    return get_project_root() / "code" / "data" / "processed" / "graphs.parquet"


def load_scarcity_flag() -> Dict[str, Any]:
    """Load the data scarcity flag."""
    flag_path = get_scarcity_flag_path()
    if not flag_path.exists():
        raise FileNotFoundError(f"Scarcity flag file not found: {flag_path}")
    
    with open(flag_path, 'r') as f:
        return json.load(f)


def load_processed_graphs() -> pd.DataFrame:
    """Load the processed graphs dataframe."""
    graphs_path = get_processed_graphs_path()
    if not graphs_path.exists():
        raise FileNotFoundError(f"Processed graphs file not found: {graphs_path}")
    
    return pd.read_parquet(graphs_path)


def select_median_barrier_sample(graphs_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Select the sample with the median barrier height.
    
    Args:
        graphs_df: DataFrame containing processed graphs with barrier_height column.
        
    Returns:
        Dictionary containing the selected sample's data.
    """
    if 'barrier_height' not in graphs_df.columns:
        raise KeyError("Column 'barrier_height' not found in graphs dataframe")
    
    # Calculate median barrier height
    median_barrier = graphs_df['barrier_height'].median()
    
    # Find sample(s) closest to median
    # If multiple, pick the first one
    closest_idx = (graphs_df['barrier_height'] - median_barrier).abs().idxmin()
    sample = graphs_df.loc[closest_idx].to_dict()
    
    logger.info(f"Selected sample with barrier height: {sample['barrier_height']:.4f} (Median: {median_barrier:.4f})")
    
    return sample


def generate_xyz_from_sample(sample: Dict[str, Any]) -> str:
    """
    Generate XYZ format string from sample data.
    
    Args:
        sample: Dictionary containing atomic numbers and coordinates.
        
    Returns:
        XYZ format string ready for PSI4 input.
    """
    if 'atomic_numbers' not in sample or 'coordinates' not in sample:
        raise KeyError("Sample missing 'atomic_numbers' or 'coordinates'")
    
    atomic_numbers = sample['atomic_numbers']
    coordinates = sample['coordinates']
    
    if len(atomic_numbers) != len(coordinates):
        raise ValueError("Mismatch between atomic_numbers and coordinates lengths")
    
    # Convert to numpy arrays if needed
    atomic_numbers = np.array(atomic_numbers)
    coordinates = np.array(coordinates)
    
    # Build XYZ string
    n_atoms = len(atomic_numbers)
    xyz_lines = [str(n_atoms)]
    xyz_lines.append("DFT benchmark calculation")
    
    # PSI4 expects element symbols, but we have atomic numbers
    # We'll use atomic numbers directly as PSI4 can handle them in internal coords
    # Actually, let's convert to element symbols for clarity
    from periodictable import elements
    
    for i in range(n_atoms):
        atomic_num = int(atomic_numbers[i])
        element = elements[atomic_num]
        x, y, z = coordinates[i]
        xyz_lines.append(f"{element.symbol} {x:.6f} {y:.6f} {z:.6f}")
    
    return "\n".join(xyz_lines)


def run_psi4_dft(xyz_content: str) -> float:
    """
    Run a single-point DFT calculation using PSI4.
    
    Args:
        xyz_content: XYZ format string of the molecule.
        
    Returns:
        Computation time in seconds.
        
    Raises:
        Exception: If PSI4 calculation fails.
    """
    # Configure PSI4
    psi4.set_memory('2 GB')
    psi4.set_num_threads(4)
    
    # Set basis set from config (default: sto-3g)
    basis_set = config.get('PSI4_BASIS', 'sto-3g')
    
    logger.info(f"Running PSI4 calculation with B3LYP/{basis_set}")
    
    start_time = time.time()
    
    try:
        # Create molecule object from XYZ
        mol = psi4.geometry(xyz_content)
        
        # Run single-point energy calculation
        # B3LYP functional with specified basis
        energy = psi4.energy('b3lyp', basis=basis_set, molecule=mol)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"PSI4 calculation completed. Energy: {energy:.6f} Ha, Time: {duration:.2f}s")
        
        return duration
        
    except Exception as e:
        logger.error(f"PSI4 calculation failed: {str(e)}")
        raise


def save_benchmark_cache(reference_time: float, sample_info: Dict[str, Any]) -> None:
    """
    Save the DFT benchmark results to cache file.
    
    Args:
        reference_time: Computation time in seconds.
        sample_info: Information about the sample used for benchmarking.
    """
    cache_path = get_cache_path()
    
    # Ensure results directory exists
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    cache_data = {
        "reference_time_seconds": reference_time,
        "sample_barrier_height": sample_info.get('barrier_height'),
        "sample_id": sample_info.get('sample_id', 'unknown'),
        "method": "B3LYP",
        "basis": config.get('PSI4_BASIS', 'sto-3g'),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(cache_path, 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    logger.info(f"Benchmark cache saved to: {cache_path}")


def run_dft_benchmark() -> Dict[str, Any]:
    """
    Main execution function for DFT benchmark.
    
    Returns:
        Dictionary containing benchmark results.
    """
    logger.info("Starting DFT benchmark execution (T036b)")
    
    # Step 1: Check scarcity flag
    logger.info("Checking data scarcity flag...")
    try:
        scarcity_flag = load_scarcity_flag()
    except FileNotFoundError as e:
        logger.warning(f"Scarcity flag not found, assuming sufficient data: {e}")
        scarcity_flag = {"status": "sufficient", "count": 0, "threshold": config.get('THRESHOLD_DATA_SCARCITY', 120)}
    
    if scarcity_flag.get('status') == 'scarcity':
        logger.warning("Data scarcity detected. Skipping DFT benchmark as per gating logic.")
        return {
            "status": "skipped",
            "reason": "data_scarcity",
            "flag": scarcity_flag
        }
    
    logger.info(f"Data status: {scarcity_flag.get('status')}")
    
    # Step 2: Load processed graphs
    logger.info("Loading processed graphs...")
    try:
        graphs_df = load_processed_graphs()
    except FileNotFoundError as e:
        logger.error(f"Failed to load processed graphs: {e}")
        raise
    
    if graphs_df.empty:
        logger.error("Processed graphs dataframe is empty")
        raise ValueError("No data available for benchmark")
    
    # Step 3: Select median barrier sample
    logger.info("Selecting median barrier sample...")
    sample = select_median_barrier_sample(graphs_df)
    
    # Step 4: Generate XYZ and run PSI4
    logger.info("Generating XYZ structure...")
    try:
        xyz_content = generate_xyz_from_sample(sample)
    except KeyError as e:
        logger.error(f"Failed to generate XYZ: {e}")
        raise
    
    logger.info("Running PSI4 DFT calculation...")
    try:
        reference_time = run_psi4_dft(xyz_content)
    except Exception as e:
        logger.error(f"PSI4 execution failed: {e}")
        raise
    
    # Step 5: Save results
    logger.info("Saving benchmark cache...")
    save_benchmark_cache(reference_time, sample)
    
    result = {
        "status": "completed",
        "reference_time_seconds": reference_time,
        "sample_barrier_height": sample.get('barrier_height'),
        "method": "B3LYP",
        "basis": config.get('PSI4_BASIS', 'sto-3g')
    }
    
    logger.info(f"DFT benchmark completed successfully. Time: {reference_time:.2f}s")
    return result


def main() -> int:
    """Main entry point for the script."""
    try:
        result = run_dft_benchmark()
        
        if result.get('status') == 'skipped':
            print(f"Benchmark skipped: {result.get('reason')}")
            return 0
        
        print(f"Benchmark completed: {result['reference_time_seconds']:.2f} seconds")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except KeyError as e:
        logger.error(f"Missing required data: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
