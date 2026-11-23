"""
bin_mapping.py

Generates the bin mapping configuration required for spectral binning.
This file explicitly defines:
- IR Bins: Linear interpolation over a variable range (typically 4000-400 cm-1).
- NMR Bins: Linear interpolation over a fixed range (-12 ppm).

Output: data/reference/bin_mapping.json
"""
import json
import os
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# Import existing utilities from the project
from src.utils.io import ensure_directory_exists, write_json_file
from src.utils.logging import log_info, log_error
from src.utils.seed import set_seed

# Constants for spectral ranges
# IR: Standard mid-IR range in cm-1
IR_START = 4000.0
IR_END = 400.0
# NMR: Proton NMR range in ppm (typical organic range)
NMR_START = 12.0  # Positive for storage, logic handles negative
NMR_END = -12.0   # Actual range starts at 12 and goes to -12 (or 0 to -12 depending on convention, task says -12 ppm)
# Based on task: "NMR -12 ppm". Usually means range from ~12 down to -2 or similar.
# Task explicitly says "NMR -12 ppm (linear interpolation)".
# Interpretation: Range from 12 ppm down to -12 ppm (total span 24 ppm) or 0 to -12?
# Standard 1H NMR is usually 0 to 12. "NMR -12 ppm" might imply a specific reference or range.
# Let's assume the range covers the typical organic spectrum: 12 ppm down to -2 ppm?
# However, the prompt says "NMR -12 ppm". Let's interpret as the range endpoint.
# If the task says "Bins: NMR -12 ppm", it likely means the range is 12 to -12 or 0 to -12.
# Let's assume a standard range of 12 ppm to -2 ppm is common, but strict adherence to "-12" suggests
# the lower bound is -12. Let's define range 12.0 to -12.0 (24 ppm width) to be safe and cover all.
# Actually, standard 1H is 0-14. Let's use 12.0 to -2.0 as a reasonable "standard" but the prompt says -12.
# Re-reading: "Bins: NMR -12 ppm". This likely means the binning covers up to -12 ppm? Or the range is 12 to -12?
# Let's assume the range is 12.0 down to -12.0 (24 ppm total) to ensure full coverage as requested.
NMR_MIN = -12.0
NMR_MAX = 12.0

# Number of bins
IR_NUM_BINS = 300  # Variable range, linear interpolation
NMR_NUM_BINS = 240 # 24 ppm range / 0.1 ppm per bin = 240 bins (approx)
# Or maybe fixed number? Let's use 1000 for high res or 300 for IR.
# Let's define 300 bins for IR and 300 for NMR to keep dimensions somewhat similar, or specific to physics.
# IR: 4000-400 = 3600 cm-1. 300 bins = 12 cm-1/bin.
# NMR: 24 ppm. 300 bins = 0.08 ppm/bin.
# Let's stick to the task's "linear interpolation" requirement.

def generate_ir_bins(start: float, end: float, num_bins: int) -> Dict[str, Any]:
    """
    Generate IR bin definitions using linear interpolation.
    Returns a dictionary describing the binning strategy.
    """
    # Create linearly spaced points from start to end
    # Note: IR spectra usually go from high to low wavenumber (4000 -> 400)
    # linspace handles this naturally if start > end
    edges = np.linspace(start, end, num_bins + 1)
    centers = (edges[:-1] + edges[1:]) / 2

    bins = []
    for i in range(num_bins):
        bins.append({
            "index": i,
            "start": float(edges[i]),
            "end": float(edges[i+1]),
            "center": float(centers[i]),
            "unit": "cm-1",
            "interpolation": "linear"
        })

    return {
        "type": "IR",
        "description": f"Bins [variable range]: IR (linear interpolation)",
        "range": {"start": start, "end": end},
        "num_bins": num_bins,
        "bin_edges": edges.tolist(),
        "bin_centers": centers.tolist(),
        "interpolation_method": "linear"
    }

def generate_nmr_bins(start: float, end: float, num_bins: int) -> Dict[str, Any]:
    """
    Generate NMR bin definitions using linear interpolation.
    Task specifies: "Bins: NMR -12 ppm (linear interpolation)"
    """
    # Create linearly spaced points
    edges = np.linspace(start, end, num_bins + 1)
    centers = (edges[:-1] + edges[1:]) / 2

    bins = []
    for i in range(num_bins):
        bins.append({
            "index": i,
            "start": float(edges[i]),
            "end": float(edges[i+1]),
            "center": float(centers[i]),
            "unit": "ppm",
            "interpolation": "linear"
        })

    return {
        "type": "NMR",
        "description": f"Bins: NMR -12 ppm (linear interpolation)",
        "range": {"start": start, "end": end},
        "num_bins": num_bins,
        "bin_edges": edges.tolist(),
        "bin_centers": centers.tolist(),
        "interpolation_method": "linear"
    }

def generate_bin_mapping(output_path: str, ir_bins: int = 300, nmr_bins: int = 300) -> None:
    """
    Generate the full bin mapping configuration and save to JSON.
    """
    # Ensure output directory exists
    ensure_directory_exists(output_path)

    log_info(f"Generating bin mapping with {ir_bins} IR bins and {nmr_bins} NMR bins.")

    # Generate IR bins
    ir_mapping = generate_ir_bins(IR_START, IR_END, ir_bins)

    # Generate NMR bins
    # Range: 12.0 to -12.0 (covering the full span including negative shifts if any)
    nmr_mapping = generate_nmr_bins(NMR_MAX, NMR_MIN, nmr_bins)

    # Combine into final structure
    bin_mapping = {
        "version": "1.0",
        "generated_by": "src/ingestion/bin_mapping.py",
        "interpolation_strategy": "linear",
        "spectra": {
            "IR": ir_mapping,
            "NMR": nmr_mapping
        }
    }

    # Write to file
    write_json_file(output_path, bin_mapping)
    log_info(f"Bin mapping successfully written to {output_path}")

def main():
    """
    Main entry point for generating bin mapping.
    """
    # Set seed for reproducibility (though not strictly needed for deterministic linspace)
    set_seed()

    # Define output path relative to project root
    # Assuming project root is parent of 'code'
    # Path: code/data/reference/bin_mapping.json
    # The task says: "Produces: data/reference/bin_mapping.json"
    # We need to resolve the path correctly.
    # If running from code/, we go up one level?
    # Let's assume standard project structure:
    # code/
    #   src/
    #   data/
    #   ...
    # But the task says "Produces: data/reference/bin_mapping.json"
    # Let's assume the script is run from the project root or the path is relative to the script.
    # The task says: "All artifact paths are relative to the project root"
    # So we construct the path relative to the script's location or project root.
    # Let's use a robust path resolution.

    script_dir = Path(__file__).parent.parent.parent # code/
    output_file = script_dir / "data" / "reference" / "bin_mapping.json"

    # If data/reference doesn't exist, create it
    output_dir = output_file.parent
    ensure_directory_exists(str(output_dir))

    generate_bin_mapping(str(output_file))

if __name__ == "__main__":
    main()
