"""
T019d: Seed Map Generation

Generates a seed map file `data/sweep/seed_map.json` that maps each unique
(n, p, rho, distribution_type) tuple to a list of deterministic integer seeds.

Dependency: T017 (params.csv), T011a (power_analysis_result.json)
Output: data/sweep/seed_map.json
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path to allow imports from utils if needed,
# though this task primarily reads/writes files.
sys.path.insert(0, str(Path(__file__).parent))

from utils.exceptions import SimulationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_master_seed() -> int:
    """
    Loads the master seed from data/sweep/master_seed.txt.
    """
    master_seed_path = Path("data/sweep/master_seed.txt")
    if not master_seed_path.exists():
        logger.error(f"Master seed file not found at {master_seed_path}.")
        raise FileNotFoundError(f"Master seed file not found at {master_seed_path}")

    with open(master_seed_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            raise ValueError("Master seed file is empty.")
        return int(content)

def load_params() -> List[Dict[str, Any]]:
    """
    Loads parameter rows from data/sweep/params.csv (output of T017).
    Returns a list of dictionaries.
    """
    params_path = Path("data/sweep/params.csv")
    if not params_path.exists():
        logger.error(f"Params file not found at {params_path}. Run T017 first.")
        raise FileNotFoundError(f"Params file not found at {params_path}. Run T017 first.")

    params = []
    with open(params_path, 'r', encoding='utf-8') as f:
        # Skip header
        header = f.readline().strip().split(',')
        if header != ['seed', 'n', 'p', 'rho', 'distribution_type', 'iteration']:
            logger.warning(f"Unexpected header in params.csv: {header}")
            # Attempt to parse anyway if structure is close, but strict check is safer
            # Reset file pointer to re-read if needed, but for now just proceed with index mapping
            # Assuming standard T017 output: seed,n,p,rho,distribution_type,iteration
            pass

        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) < 6:
                logger.warning(f"Skipping malformed line in params.csv: {line}")
                continue

            row = {
                'seed': int(parts[0]),
                'n': int(parts[1]),
                'p': int(parts[2]),
                'rho': float(parts[3]),
                'distribution_type': parts[4],
                'iteration': int(parts[5])
            }
            params.append(row)

    return params

def load_required_iterations() -> int:
    """
    Loads the required iteration count from data/sweep/power_analysis_result.json (output of T011a).
    """
    result_path = Path("data/sweep/power_analysis_result.json")
    if not result_path.exists():
        logger.error(f"Power analysis result not found at {result_path}. Run T011a first.")
        raise FileNotFoundError(f"Power analysis result not found at {result_path}. Run T011a first.")

    with open(result_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'iterations' not in data:
        raise KeyError("Power analysis result missing 'iterations' key.")

    return data['iterations']

def build_seed_map(params: List[Dict[str, Any]], required_iterations: int) -> Dict[str, List[int]]:
    """
    Builds the seed map by grouping parameters and assigning seeds.

    Algorithm:
    1. Identify unique (n, p, rho, distribution_type) tuples.
    2. For each unique tuple, count how many iterations (rows in params) exist.
    3. Verify count == required_iterations.
    4. Assign sequential seeds starting from master_seed + offset.
    """
    # Group by unique key
    grouped = {}
    for row in params:
        key = (row['n'], row['p'], row['rho'], row['distribution_type'])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(row)

    seed_map = {}
    # We need to assign seeds sequentially. The task says:
    # "for each parameter combination, assign sequential seeds starting at the master seed
    # and incrementing by 1 for each required simulation iteration"
    # This implies a global counter or a per-group counter?
    # "T017 generates the seeds; T019d organizes them."
    # T017 formula: seed = master_seed + (index * 10000) + ...
    # But T019d says: "assign sequential seeds starting at the master seed and incrementing by 1"
    # This sounds like a simple range per group.
    # Let's assume the "seed map" needs to list the seeds that T017 would have generated
    # OR T019d generates a NEW set of seeds that are strictly sequential per group.
    # Given the dependency "T017 generates the seeds", T019d should likely RECONSTRUCT
    # the seeds based on the master seed and the iteration count to ensure T022a can use them.
    # However, the task description for T019d says: "assign sequential seeds starting at the master seed"
    # This is slightly ambiguous if there are multiple groups.
    # Interpretation: Each group gets a contiguous block of seeds.
    # Group 1: master_seed ... master_seed + N-1
    # Group 2: master_seed + N ... master_seed + 2N - 1
    # This ensures deterministic, non-overlapping seeds for every simulation run.

    master_seed = load_master_seed()
    current_seed = master_seed

    for key, rows in grouped.items():
        count = len(rows)
        if count != required_iterations:
            error_msg = (
                f"Seed map mismatch for {key}: "
                f"Found {count} rows in params.csv, but required {required_iterations} iterations."
            )
            logger.error(error_msg)
            raise SimulationError(error_msg)

        # Generate the list of seeds for this group
        # We use a simple range: current_seed to current_seed + count
        # This creates a deterministic sequence for this specific parameter set.
        seeds = list(range(current_seed, current_seed + count))
        seed_map[str(key)] = seeds

        current_seed += count

    return seed_map

def write_seed_map(seed_map: Dict[str, List[int]], output_path: str = "data/sweep/seed_map.json") -> None:
    """
    Writes the seed map to the specified JSON file.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(seed_map, f, indent=2)

    logger.info(f"Seed map written to {output_path}")

def main():
    """
    Main entry point for T019d.
    """
    try:
        logger.info("Starting T019d: Seed Map Generation")

        # 1. Load dependencies
        required_iterations = load_required_iterations()
        logger.info(f"Required iterations: {required_iterations}")

        params = load_params()
        logger.info(f"Loaded {len(params)} parameter rows from params.csv")

        # 2. Build seed map
        seed_map = build_seed_map(params, required_iterations)
        logger.info(f"Built seed map with {len(seed_map)} unique parameter combinations")

        # 3. Write output
        write_seed_map(seed_map)

        logger.info("T019d completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Missing dependency file: {e}")
        sys.exit(1)
    except SimulationError as e:
        logger.error(f"Simulation error (Seed Map Mismatch): {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
