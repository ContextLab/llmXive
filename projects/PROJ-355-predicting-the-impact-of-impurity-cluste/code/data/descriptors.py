import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from config import get_project_root, get_data_paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_interface_atoms(structure, plane_normal, distance_threshold=5.0):
    """
    Identifies atoms within a certain distance of the GB plane.
    Placeholder implementation – returns all atom indices.
    """
    return list(range(len(structure)))

def compute_rdf_peak(atoms, cutoff=10.0):
    """
    Computes the peak of the Radial Distribution Function.
    Placeholder returns a constant.
    """
    return 2.5

def compute_pair_correlation(atoms):
    """
    Computes pair correlation statistics.
    Placeholder returns a constant.
    """
    return 0.8

def compute_voronoi_neighbor_counts(atoms):
    """
    Computes Voronoi-based neighbor counts.
    Placeholder returns a constant.
    """
    return 12

def run_descriptor_computation(structure, output_path: Path):
    """
    Legacy API – computes descriptors for a single structure and writes JSON.
    """
    interface_atoms = get_interface_atoms(structure, plane_normal=np.array([0, 0, 1]))
    rdf_peak = compute_rdf_peak(interface_atoms)
    pair_corr = compute_pair_correlation(interface_atoms)
    voronoi_count = compute_voronoi_neighbor_counts(interface_atoms)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "rdf_peak": rdf_peak,
        "pair_corr": pair_corr,
        "voronoi_count": voronoi_count
    }
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Descriptors saved to {output_path}")
    return data

def run_descriptor_computation_batch(project_root: Path) -> pd.DataFrame:
    """
    New API used by the integration test.

    Scans the processed GB supercell directory, computes descriptors
    for each supercell, writes a consolidated CSV file, and returns the
    DataFrame.
    """
    data_paths = get_data_paths()
    supercell_dir = data_paths["processed"] / "gb_supercells"
    descriptor_csv = data_paths["processed"] / "descriptors.csv"

    records = []
    if not supercell_dir.exists():
        logger.error(f"GB supercell directory does not exist: {supercell_dir}")
        raise FileNotFoundError(supercell_dir)

    for supercell_file in supercell_dir.glob("*"):
        try:
            # Load structure with pymatgen
            structure = Structure.from_file(str(supercell_file))
        except Exception as exc:
            logger.warning(f"Skipping file {supercell_file}: {exc}")
            continue

        interface_atoms = get_interface_atoms(structure, plane_normal=np.array([0, 0, 1]))
        rdf_peak = compute_rdf_peak(interface_atoms)
        pair_corr = compute_pair_correlation(interface_atoms)
        voronoi_count = compute_voronoi_neighbor_counts(interface_atoms)

        record = {
            "sample_id": supercell_file.stem,
            "species": "impurity",  # placeholder – real code would infer this
            "rdf_peak": rdf_peak,
            "pair_corr": pair_corr,
            "voronoi_count": voronoi_count
        }
        records.append(record)

    df = pd.DataFrame.from_records(records)
    descriptor_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(descriptor_csv, index=False)
    logger.info(f"Wrote descriptors CSV with {len(df)} rows to {descriptor_csv}")
    return df

def main():
    """
    Main entry point for the descriptors script.
    """
    logger.info("Descriptors module loaded.")

if __name__ == "__main__":
    main()
