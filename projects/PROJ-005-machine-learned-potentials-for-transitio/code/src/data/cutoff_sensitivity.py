import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd

from code.src.utils.config import get_config

logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory (parent of 'code' directory)."""
    return Path(__file__).resolve().parent.parent.parent.parent

def load_processed_graphs_intermediate() -> pd.DataFrame:
    """
    Load the intermediate processed graphs data.
    This assumes T015/T016 have created a raw/intermediate geometry file.
    Based on the task flow, we expect raw geometries or an intermediate state
    before final graph construction with a specific cutoff.
    For this analysis, we need atomic positions and connectivity info to
    calculate edge counts for different cutoffs.
    
    Since T015/T016 are marked complete, we assume the raw data is available
    in a format we can process. If the specific intermediate file isn't
    defined in the schema, we look for a standard intermediate format or
    the raw data that was ingested.
    
    Given the task description: "Input: Raw geometries from T015", we expect
    the raw data to be available. We will look for the raw data file.
    """
    root = get_project_root()
    # The raw data from T015 should be here. Assuming a parquet or csv format
    # containing atomic coordinates.
    # Based on typical pipelines, let's assume the raw data is stored as
    # 'qm9_ts_filtered.parquet' or similar in data/raw or data/processed.
    # However, T015 says it fetches and computes checksums. T016 filters.
    # The output of T016 is a count, but the data itself must exist.
    # Let's assume the filtered data is stored in data/processed/intermediate_geometries.parquet
    # or similar. If not found, we might need to re-fetch or locate the raw file.
    
    # Let's try to find the most likely location for the filtered data
    processed_dir = root / "data" / "processed"
    raw_dir = root / "data" / "raw"
    
    # Look for intermediate geometries
    candidates = [
        processed_dir / "intermediate_geometries.parquet",
        processed_dir / "filtered_geometries.parquet",
        raw_dir / "qm9_ts_filtered.parquet",
        raw_dir / "qm9-ts.parquet",
    ]
    
    for candidate in candidates:
        if candidate.exists():
            logger.info(f"Loading intermediate data from {candidate}")
            return pd.read_parquet(candidate)
    
    # If not found, check for a specific file mentioned in T015/T016 context
    # If T015 fetched from HuggingFace, the raw file might be there
    raw_files = list(raw_dir.glob("*"))
    if raw_files:
        # Assume the first parquet file is the raw data
        for f in raw_files:
            if f.suffix == '.parquet':
                logger.info(f"Loading raw data from {f}")
                return pd.read_parquet(f)
    
    raise FileNotFoundError(
        "Could not find intermediate or raw geometry data required for cutoff sensitivity analysis. "
        "Ensure T015 and T016 have successfully downloaded and filtered the data."
    )

def calculate_distance_matrix(positions: np.ndarray) -> np.ndarray:
    """Calculate pairwise Euclidean distance matrix."""
    diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
    return np.sqrt(np.sum(diff**2, axis=2))

def calculate_edge_count_for_cutoff(positions: np.ndarray, cutoff: float) -> int:
    """
    Calculate the number of edges in the graph for a given cutoff distance.
    Edges are undirected, so we count each pair once.
    """
    dist_matrix = calculate_distance_matrix(positions)
    # Create adjacency matrix where True means distance < cutoff (and not self)
    adj = (dist_matrix < cutoff) & (dist_matrix > 0)
    # Count edges (upper triangle to avoid double counting)
    return np.sum(np.triu(adj, k=1))

def run_sensitivity_analysis(graphs_df: pd.DataFrame, cutoffs: List[float]) -> Dict[str, float]:
    """
    Perform sensitivity analysis by calculating edge count variance for each cutoff.
    
    Args:
        graphs_df: DataFrame containing molecular data with atomic positions.
        cutoffs: List of cutoff distances to test.
        
    Returns:
        Dictionary mapping cutoff string to variance of edge counts.
    """
    variances = {}
    
    # Expecting the dataframe to have a column with atomic positions or a way to reconstruct them
    # Common formats: 'positions' (list of arrays), 'atoms' (list of atom dicts), etc.
    # We need to handle the specific format of the ingested data.
    # Assuming the data has a column 'atoms' or 'positions' that contains the 3D coordinates.
    
    if 'positions' in graphs_df.columns:
        # If positions are stored as a list of arrays per row
        positions_list = graphs_df['positions'].tolist()
    elif 'atomic_positions' in graphs_df.columns:
        positions_list = graphs_df['atomic_positions'].tolist()
    else:
        # Try to find any column that looks like it contains coordinates
        coord_cols = [col for col in graphs_df.columns if 'pos' in col.lower() or 'coord' in col.lower()]
        if coord_cols:
            # This is a guess; we might need to adapt based on actual data schema
            logger.warning(f"Could not find standard 'positions' column. Trying {coord_cols[0]}")
            # This might fail if the format isn't a simple list of arrays
            positions_list = graphs_df[coord_cols[0]].tolist()
        else:
            raise ValueError("Could not identify atomic positions column in the dataframe.")
    
    edge_counts = {cutoff: [] for cutoff in cutoffs}
    
    for idx, positions in enumerate(positions_list):
        if idx % 100 == 0:
            logger.info(f"Processing molecule {idx}/{len(positions_list)}")
        
        # Ensure positions is a numpy array
        if isinstance(positions, list):
            positions = np.array(positions)
        
        if positions.ndim != 2 or positions.shape[1] != 3:
            logger.warning(f"Molecule {idx} has invalid positions shape: {positions.shape}. Skipping.")
            continue
        
        for cutoff in cutoffs:
            edge_count = calculate_edge_count_for_cutoff(positions, cutoff)
            edge_counts[cutoff].append(edge_count)
    
    # Calculate variance for each cutoff
    for cutoff, counts in edge_counts.items():
        if len(counts) > 1:
            variances[str(cutoff)] = float(np.var(counts))
        else:
            variances[str(cutoff)] = 0.0
        
    return variances

def select_optimal_cutoff(variances: Dict[str, float]) -> float:
    """
    Select the cutoff that minimizes the variance of edge counts.
    Fallback to 3.5 if variances are identical.
    """
    if not variances:
        logger.warning("No variances calculated. Using default cutoff 3.5.")
        return 3.5
    
    min_variance = min(variances.values())
    candidates = [cutoff for cutoff, var in variances.items() if var == min_variance]
    
    if len(candidates) == 1:
        selected = float(candidates[0])
    else:
        # If multiple cutoffs have the same minimum variance, prefer 3.5 if available
        if "3.5" in candidates:
            selected = 3.5
        else:
            selected = float(candidates[0])
    
    # Fallback if 3.5 was not in candidates but variances were identical (unlikely with float)
    if len(candidates) > 1 and all(abs(v - min_variance) < 1e-9 for v in variances.values()):
        if 3.5 not in candidates:
            selected = 3.5
            logger.info("Variances are identical. Using fallback cutoff 3.5.")
    
    logger.info(f"Selected optimal cutoff: {selected} (variance: {variances[str(selected)]})")
    return selected

def save_results(selected_cutoff: float, variances: Dict[str, float], output_path: Path):
    """Save the sensitivity analysis results to a JSON file."""
    result = {
        "selected_cutoff": selected_cutoff,
        "variances": variances
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def run_cutoff_sensitivity_analysis():
    """Main entry point for the cutoff sensitivity analysis task."""
    # Load configuration
    config = get_config()
    cutoff_range = config.get("CUTOFF_RANGE", [3.0, 3.5, 4.0])
    
    logger.info(f"Starting cutoff sensitivity analysis with cutoffs: {cutoff_range}")
    
    # Load data
    try:
        graphs_df = load_processed_graphs_intermediate()
        logger.info(f"Loaded {len(graphs_df)} molecules for analysis")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise
    
    # Run analysis
    variances = run_sensitivity_analysis(graphs_df, cutoff_range)
    logger.info(f"Calculated variances: {variances}")
    
    # Select optimal cutoff
    selected_cutoff = select_optimal_cutoff(variances)
    
    # Save results
    root = get_project_root()
    output_path = root / "data" / "results" / "cutoff_sensitivity_raw.json"
    save_results(selected_cutoff, variances, output_path)
    
    return selected_cutoff, variances

def main():
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        run_cutoff_sensitivity_analysis()
        logger.info("Cutoff sensitivity analysis completed successfully.")
    except Exception as e:
        logger.error(f"Cutoff sensitivity analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
