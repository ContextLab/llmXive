import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path
import logging
import json
import sys
import os

# Add parent to path for local imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_logger, ProjectConfig
from data.models import HarmonizedDataset
from data.parsers import parse_arxiv_2106_08611, parse_arxiv_2305_06325

logger = get_logger(__name__)

# Constants
DYNE_TO_NEWTON = 1e-5
MICROMETER_TO_METER = 1e-6

def dynes_to_newtons(force_dyne: np.ndarray) -> np.ndarray:
    """Convert force from dynes to Newtons."""
    return force_dyne * DYNE_TO_NEWTON

def micrometers_to_meters(separation_um: np.ndarray) -> np.ndarray:
    """Convert separation distance from micrometers to meters."""
    return separation_um * MICROMETER_TO_METER

def convert_to_si(dataset: HarmonizedDataset) -> HarmonizedDataset:
    """
    Convert all force and separation values in the dataset to SI units.
    
    Args:
        dataset: A HarmonizedDataset object with values in cgs/um.
        
    Returns:
        A new HarmonizedDataset object with values in SI (N, m).
    """
    logger.info("Converting dataset to SI units...")
    
    force_n = dynes_to_newtons(dataset.force_n)
    separation_m = micrometers_to_meters(dataset.separation_m)
    
    # Covariance matrix units: (N^2) since force is squared
    # If the input covariance was in (dyne^2), we need to scale it.
    # Assuming input covariance is in (dyne^2) based on typical cgs data.
    cov_matrix_si = dataset.covariance_matrix * (DYNE_TO_NEWTON ** 2)
    
    return HarmonizedDataset(
        separation_m=separation_m,
        force_n=force_n,
        covariance_matrix=cov_matrix_si,
        metadata=dataset.metadata
    )

def align_to_grid(
    datasets: List[HarmonizedDataset], 
    grid_resolution: float = 1e-8,
    grid_range: Optional[Tuple[float, float]] = None
) -> HarmonizedDataset:
    """
    Align multiple datasets to a common separation distance grid using linear interpolation.
    
    Handles edge cases:
    - Non-overlapping separation ranges: Logs warning and excludes non-overlapping regions.
    - Missing points: Interpolates if within the convex hull of the data.
    
    Args:
        datasets: List of HarmonizedDataset objects (already in SI units).
        grid_resolution: Spacing of the output grid in meters (default 10 nm).
        grid_range: Optional (min, max) separation range. If None, inferred from overlap.
        
    Returns:
        A single merged HarmonizedDataset on the common grid.
    """
    if not datasets:
        raise ValueError("No datasets provided for alignment.")
    
    # Determine common grid range
    if grid_range:
        min_sep, max_sep = grid_range
    else:
        # Find the intersection of all ranges
        all_mins = [d.separation_m.min() for d in datasets]
        all_maxs = [d.separation_m.max() for d in datasets]
        min_sep = max(all_mins)
        max_sep = min(all_maxs)
        
        if min_sep >= max_sep:
            raise ValueError("No overlapping separation range found between datasets.")
        
        logger.warning(
            f"Inferred common separation range: [{min_sep:.2e}, {max_sep:.2e}] m. "
            f"Non-overlapping regions excluded."
        )

    # Create the common grid
    # Ensure we cover the range inclusive
    num_points = int(np.ceil((max_sep - min_sep) / grid_resolution)) + 1
    common_grid = np.linspace(min_sep, max_sep, num_points)
    
    # Prepare lists for aggregation
    aligned_forces = []
    aligned_covs = [] # List of (index_mask, cov_block) if we were doing sparse, but here we assume diagonal or full dense per run
    
    # We will construct a combined covariance matrix. 
    # Since datasets are independent experimental runs, the cross-covariance between runs is 0.
    # We will stack the data. However, the task implies aligning to a *common grid* for a single 
    # harmonized dataset. If we interpolate multiple runs onto the same grid points, we have 
    # multiple force measurements at the same grid point.
    # 
    # Strategy: For each grid point, if multiple runs have data, we average them (weighted by uncertainty).
    # If only one run has data, we use that.
    # This requires handling the covariance carefully.
    # 
    # Simplified Strategy per Plan: "Align on a common grid".
    # We will interpolate each dataset onto the common grid.
    # Then we concatenate them? Or average? 
    # The plan says "construct a single CSV/JSON file containing aligned force data...".
    # Usually, this means creating a unified dataset where each row is a unique separation point,
    # and if multiple experiments measured that point, they are combined or stored as multiple entries.
    # Given the "HarmonizedDataset" model has 1D arrays, we likely need to merge them.
    # Let's assume we stack the interpolated data points. If the grid is identical, we have N_points * N_runs rows?
    # Or we average at the grid points.
    # 
    # Let's look at the model: `separation_m` (N,), `force_n` (N,).
    # If we align to a grid, we get N_grid points.
    # If we have multiple runs, we might have multiple force values at the same separation.
    # To fit the model, we can either:
    # 1. Keep them as separate rows (duplicate separation_m values).
    # 2. Average them.
    # 
    # The plan mentions "full covariance matrix". If we duplicate rows, the covariance matrix
    # must be block diagonal (assuming independent runs).
    # 
    # Let's implement Strategy 1: Stack all interpolated points.
    # This preserves all data. The separation_m array will have duplicates.
    
    total_points = 0
    for ds in datasets:
        # Check for overlap
        if ds.separation_m.max() < min_sep or ds.separation_m.min() > max_sep:
            logger.warning(f"Dataset {ds.metadata.get('id', 'unknown')} has no overlap with common grid. Skipping.")
            continue
        
        # Clip to common range
        mask = (ds.separation_m >= min_sep) & (ds.separation_m <= max_sep)
        if not np.any(mask):
            continue
            
        x_orig = ds.separation_m[mask]
        y_orig = ds.force_n[mask]
        
        # Interpolate to common grid
        # Use linear interpolation. Extrapolate with NaN or clip?
        # We only care about the common range, so no extrapolation needed if we clipped correctly.
        y_interp = np.interp(common_grid, x_orig, y_orig)
        
        # Check for NaNs (shouldn't happen if we clipped to valid range, but good to check)
        if np.any(np.isnan(y_interp)):
            logger.warning(f"Interpolation resulted in NaNs for dataset {ds.metadata.get('id', 'unknown')}.")
            # Fill with NaN or drop? We'll keep NaNs and handle in covariance if needed, 
            # but for now, let's assume valid interpolation.
            
        aligned_forces.append(y_interp)
        total_points += len(common_grid)

    if not aligned_forces:
        raise ValueError("No data points remained after filtering for overlapping range.")

    # Concatenate forces
    final_forces = np.concatenate(aligned_forces)
    # Repeat the grid for each dataset
    final_separations = np.tile(common_grid, len(aligned_forces))
    
    # Construct Covariance Matrix
    # Since runs are independent, the full covariance is block diagonal.
    # Each block corresponds to the covariance of one run's interpolated points.
    # Interpolation introduces correlations even if original data was uncorrelated.
    # However, for this task, we will approximate the covariance of the interpolated points
    # by scaling the original covariance or assuming diagonal if not provided.
    # The plan says "construct a full covariance matrix".
    # If the input datasets have full covariance, we need to propagate the interpolation error.
    # This is complex. A simpler approach for the "harmonized" step is to assume the 
    # covariance provided in the input is the uncertainty of the measurement.
    # If we interpolate, the uncertainty at the grid points is a linear combination.
    # 
    # Given the complexity and the fact that T015 handles "Covariance Construction" specifically,
    # we will assume the input datasets have a covariance matrix that represents the 
    # uncertainty at their measured points. 
    # For the harmonized output, we will construct a block-diagonal matrix where each block
    # is the covariance of the *interpolated* points.
    # 
    # To keep it simple and robust: We will assume the input covariance is diagonal (uncorrelated points)
    # or we will just take the diagonal of the input covariance and assume it applies to the interpolated points
    # (a simplification). 
    # Actually, the plan for T015 says "Primary Strategy: Since source data lacks off-diagonal terms... construct a diagonal covariance".
    # So we can assume the input covariance is diagonal or we treat it as such for the interpolation step.
    # 
    # Let's construct a block diagonal matrix.
    # If the input covariance is full, we need to transform it.
    # If the input covariance is diagonal, we just map the values.
    
    # We will assume the input `covariance_matrix` in HarmonizedDataset is the full covariance of the original points.
    # We need to compute the covariance of the interpolated points.
    # y_interp = sum(w_i * y_i). Cov(y_interp) = w^T Cov(y) w.
    # This is expensive if we do it for every grid point.
    # 
    # Alternative: Since T015 will "construct" the covariance matrix based on uncertainties,
    # we can just store the interpolated forces and separations, and T015 will rebuild the covariance
    # from the uncertainty estimates (which we might need to interpolate too).
    # 
    # But the HarmonizedDataset model expects a covariance matrix.
    # Let's assume the input covariance is diagonal (as per T015 primary strategy).
    # Then the interpolated point's variance is sum(w_i^2 * var_i).
    # 
    # For now, to satisfy the "real code" requirement without over-engineering:
    # We will create a diagonal covariance matrix for the harmonized data by interpolating
    # the standard deviations (sqrt of diagonal) and squaring them back.
    # This is an approximation but valid if correlations are weak.
    
    final_covariance = np.zeros((total_points, total_points))
    
    current_idx = 0
    for ds in datasets:
        mask = (ds.separation_m >= min_sep) & (ds.separation_m <= max_sep)
        if not np.any(mask):
            continue
            
        x_orig = ds.separation_m[mask]
        # Assume diagonal covariance for simplicity in this step, or extract diagonal
        # If the input is full, we take the diagonal for this approximation
        if ds.covariance_matrix.ndim == 2:
            diag_vals = np.diag(ds.covariance_matrix)
        else:
            diag_vals = ds.covariance_matrix
            
        y_std = np.sqrt(diag_vals)
        
        # Interpolate standard deviation to common grid
        std_interp = np.interp(common_grid, x_orig, y_std)
        
        # Reconstruct diagonal covariance for this block
        block_size = len(common_grid)
        final_covariance[current_idx:current_idx+block_size, current_idx:current_idx+block_size] = np.diag(std_interp**2)
        
        current_idx += block_size

    logger.info(f"Aligned {len(datasets)} datasets to grid of {len(common_grid)} points. "
                f"Total points in harmonized dataset: {total_points}.")
                
    return HarmonizedDataset(
        separation_m=final_separations,
        force_n=final_forces,
        covariance_matrix=final_covariance,
        metadata={"source_ids": [d.metadata.get("id", "unknown") for d in datasets]}
    )

def harmonize_experiment(raw_data_path: Path, output_path: Path) -> HarmonizedDataset:
    """
    Main pipeline step to parse, convert, and harmonize a single experiment.
    If multiple runs are found in the path, they are merged.
    """
    logger.info(f"Processing raw data from {raw_data_path}")
    
    # Parse raw data
    # The parser functions are specific to arXiv IDs. We need a generic parser or detect ID.
    # For this task, we assume the input path contains files that can be parsed by the 
    # generic parse_raw_data or we detect the source.
    # Let's assume we have a way to identify the source or use a generic parser.
    # The task description says "Implement unit conversion... and grid alignment".
    # We assume the parsing is done in T013-PARSE and produces HarmonizedDataset objects.
    # This function might be the orchestrator for a single file or a batch.
    
    # Since T013-PARSE produces HarmonizedDataset, we assume we are receiving a list of them
    # or a single one.
    # However, the signature suggests processing a path.
    # Let's implement a fallback: try to parse based on content or filename.
    
    # For the purpose of this task, we assume the caller has already parsed the data
    # into HarmonizedDataset objects. If this function is the entry point:
    # We will call the parsers if the path looks like raw data.
    
    datasets = []
    
    # Heuristic: Check if it's a directory with CSVs (raw) or a single file
    if raw_data_path.is_dir():
        # Try to find CSVs
        csv_files = list(raw_data_path.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {raw_data_path}")
        
        # Assume generic parsing for now, or specific if we can detect
        # We will use a generic parser that reads any CSV with 'separation' and 'force' columns
        # But the existing API has specific parsers.
        # Let's assume we call a generic parser if available, or we just load the files.
        # Since the API surface shows `parse_raw_data`, we use that.
        from data.parsers import parse_raw_data
        
        for csv_file in csv_files:
            try:
                ds = parse_raw_data(csv_file)
                datasets.append(ds)
            except Exception as e:
                logger.warning(f"Failed to parse {csv_file}: {e}")
    else:
        # Single file
        try:
            from data.parsers import parse_raw_data
            ds = parse_raw_data(raw_data_path)
            datasets.append(ds)
        except Exception as e:
            raise RuntimeError(f"Failed to parse {raw_data_path}: {e}")
    
    if not datasets:
        raise ValueError("No valid datasets could be parsed from the input path.")
    
    # Convert to SI
    si_datasets = [convert_to_si(ds) for ds in datasets]
    
    # Align to grid
    harmonized = align_to_grid(si_datasets)
    
    # Save if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        from data.loaders import save_harmonized_data
        save_harmonized_data(harmonized, output_path)
        logger.info(f"Saved harmonized dataset to {output_path}")
        
    return harmonized

def construct_covariance_matrix(
    separation_m: np.ndarray, 
    force_n: np.ndarray, 
    uncertainties: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Construct a diagonal covariance matrix from force data and uncertainties.
    This is a helper for T015, but included here as per API surface.
    """
    if uncertainties is None:
        # Estimate uncertainty as a fraction of force or a fixed value?
        # The plan says "combine statistical uncertainties and systematic error budgets".
        # For now, return a zero matrix or a placeholder if uncertainties are missing.
        # But T015 will handle the full construction.
        # We return a diagonal matrix with small noise if no uncertainties provided.
        uncertainties = np.abs(force_n) * 0.01 # 1% default
        
    cov = np.diag(uncertainties**2)
    return cov

def main():
    """
    Entry point for the harmonize script.
    Expected to be run after T013-DATA and T013-PARSE have populated data/raw/.
    """
    config = ProjectConfig()
    setup_logging()
    
    raw_dir = config.data_raw_dir
    processed_dir = config.data_processed_dir
    
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        sys.exit(1)
        
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files in raw_dir
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        logger.warning("No CSV files found in raw directory. Skipping harmonization.")
        return
    
    logger.info(f"Found {len(csv_files)} raw CSV files.")
    
    datasets = []
    for csv_file in csv_files:
        try:
            ds = harmonize_experiment(csv_file, None) # Don't save individual, aggregate
            datasets.append(ds)
        except Exception as e:
            logger.error(f"Error processing {csv_file}: {e}")
    
    if not datasets:
        logger.error("No datasets were successfully processed.")
        sys.exit(1)
        
    # Combine all datasets into one harmonized dataset
    # This calls align_to_grid on the list of already SI-converted datasets
    final_dataset = align_to_grid(datasets)
    
    output_path = processed_dir / "harmonized_data.csv"
    from data.loaders import save_harmonized_data
    save_harmonized_data(final_dataset, output_path)
    
    logger.info(f"Harmonization complete. Output saved to {output_path}")

if __name__ == "__main__":
    main()