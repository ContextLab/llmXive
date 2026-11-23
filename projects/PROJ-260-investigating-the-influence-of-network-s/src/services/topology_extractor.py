import ase
import numpy as np
from scipy.spatial import distance_matrix
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from ase.io import stream
from itertools import islice
import json
import os

from src.models.bond_network import BondNetwork
from src.models.simulation_box import SimulationBox
from src.lib.config import get_config

# Configure logging
logger = logging.getLogger(__name__)

def setup_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """Setup a logger that writes to both stdout and a file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger

def calculate_rdf(
    atoms: ase.Atoms,
    cutoff: float,
    nbins: int = 200
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate the Radial Distribution Function (RDF) for a given cutoff.
    Returns distances and g(r) values.
    """
    positions = atoms.get_positions()
    n_atoms = len(positions)
    box = atoms.get_cell()
    pbc = atoms.get_pbc()

    # Use ASE's built-in distance calculation with PBC
    distances = []
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            d = atoms.get_distance(i, j, mic=True)
            if d < cutoff:
                distances.append(d)

    if not distances:
        return np.array([]), np.array([])

    distances = np.array(distances)
    hist, bin_edges = np.histogram(distances, bins=nbins, range=(0, cutoff))

    # Normalize by volume of shells
    r = (bin_edges[:-1] + bin_edges[1:]) / 2
    dr = bin_edges[1] - bin_edges[0]
    volumes = 4 * np.pi * r**2 * dr

    # Normalize by number of pairs and density
    rho = n_atoms / atoms.get_volume()
    g_r = hist / (volumes * rho * n_atoms / 2)

    return r, g_r

def determine_cutoff(
    r: np.ndarray,
    g_r: np.ndarray,
    min_r: float = 2.0,
    max_r: float = 5.0
) -> float:
    """
    Determine the bond cutoff by finding the first local minimum of the RDF.
    """
    if len(r) == 0 or len(g_r) == 0:
        raise ValueError("Empty RDF data provided")

    # Filter to relevant range
    mask = (r >= min_r) & (r <= max_r)
    r_filtered = r[mask]
    g_filtered = g_r[mask]

    if len(r_filtered) < 3:
        logger.warning("RDF range too small, using default cutoff 3.0")
        return 3.0

    # Find local minima
    from scipy.signal import argrelextrema
    minima_idx = argrelextrema(g_filtered, np.less)[0]

    if len(minima_idx) == 0:
        logger.warning("No local minimum found, using first minimum of range")
        return r_filtered[np.argmin(g_filtered)]

    # Get the first minimum
    first_min_idx = minima_idx[0]
    cutoff = r_filtered[first_min_idx]

    # Check for ambiguity (shallow minimum)
    peak_height = np.max(g_filtered[:first_min_idx]) if first_min_idx > 0 else 1.0
    min_depth = g_filtered[first_min_idx]
    relative_depth = (peak_height - min_depth) / peak_height if peak_height > 0 else 0

    if relative_depth < 0.05:
        logger.warning(f"CRITICAL: Ambiguous RDF Minimum detected (depth={relative_depth:.2%}). "
                     f"Using detected cutoff {cutoff:.3f} Å.")
        # Check for multiple minima within 0.2 Å
        nearby_minima = [i for i in minima_idx if abs(r_filtered[i] - cutoff) < 0.2]
        if len(nearby_minima) > 1:
            logger.warning(f"Multiple minima found within 0.2 Å range. Ambiguity confirmed.")

    return cutoff

def construct_bond_network(
    atoms: ase.Atoms,
    cutoff: float
) -> BondNetwork:
    """
    Construct a bond network based on a distance cutoff.
    """
    positions = atoms.get_positions()
    n_atoms = len(positions)
    box = atoms.get_cell()
    pbc = atoms.get_pbc()

    # Calculate all pairwise distances
    dist_matrix = atoms.get_all_distances(mic=True)

    # Create adjacency matrix
    adjacency = (dist_matrix < cutoff) & (dist_matrix > 0)

    # Extract edges
    edges = []
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            if adjacency[i, j]:
                edges.append((i, j))

    # Create simulation box
    sim_box = SimulationBox(
        positions=positions,
        box_vectors=np.array(box),
        pbc=pbc
    )

    # Create bond network
    bond_network = BondNetwork(
        simulation_box=sim_box,
        edges=edges
    )

    return bond_network

def compute_coordination_number(bond_network: BondNetwork) -> np.ndarray:
    """
    Compute coordination number for each atom.
    """
    return bond_network.get_coordination_numbers()

def compute_bond_angle_variance(bond_network: BondNetwork) -> np.ndarray:
    """
    Compute bond angle variance for each atom.
    """
    return bond_network.get_bond_angle_variance()

def extract_topology(
    trajectory_path: Path,
    output_path: Path,
    rdf_override: Optional[float] = None,
    chunk_size: int = 10000,
    sample_limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Extract topology from a trajectory file with streaming support.

    Args:
        trajectory_path: Path to the trajectory file
        output_path: Path to write the output CSV
        rdf_override: Optional override for RDF cutoff
        chunk_size: Number of atoms to process at a time (for streaming)
        sample_limit: Maximum number of frames to process (for large files)

    Returns:
        Dictionary with extraction statistics
    """
    logger = setup_logger("topology_extractor", Path("data/metadata/topology_log.log"))
    logger.info(f"Starting topology extraction from {trajectory_path}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check file size for streaming decision
    file_size = os.path.getsize(trajectory_path)
    use_streaming = file_size > 100 * 1024 * 1024  # > 100MB

    if use_streaming:
        logger.info(f"Large file detected ({file_size / 1024 / 1024:.1f} MB). Using streaming.")

    # Initialize counters
    total_atoms = 0
    processed_frames = 0
    anomaly_count = 0
    cutoff_used = None

    # Prepare output data
    output_data = []

    # Determine sampling strategy
    sampling_info = {
        "used_sampling": False,
        "sample_size": 0,
        "reason": ""
    }

    try:
        if use_streaming:
            # Use ASE stream for chunked reading
            frames = stream.iread(
                str(trajectory_path),
                format=trajectory_path.suffix.strip('.'),
                chunk_size=chunk_size
            )

            if sample_limit:
                logger.info(f"Sampling limited to {sample_limit} frames for large dataset.")
                sampling_info["used_sampling"] = True
                sampling_info["sample_size"] = sample_limit
                sampling_info["reason"] = "Large file streaming with limit"
                frames = islice(frames, sample_limit)

            for frame_idx, atoms in enumerate(frames):
                processed_frames += 1
                total_atoms += len(atoms)

                # Determine cutoff
                if rdf_override:
                    cutoff = rdf_override
                    logger.info(f"Using override cutoff: {cutoff:.3f} Å")
                else:
                    r, g_r = calculate_rdf(atoms, cutoff=5.0)
                    if len(r) > 0:
                        cutoff = determine_cutoff(r, g_r)
                        logger.debug(f"Detected cutoff: {cutoff:.3f} Å")
                    else:
                        cutoff = 3.0
                        logger.warning("Could not calculate RDF, using default cutoff 3.0 Å")

                if cutoff_used is None:
                    cutoff_used = cutoff

                # Construct bond network
                bond_network = construct_bond_network(atoms, cutoff)

                # Compute metrics
                coord_nums = compute_coordination_number(bond_network)
                angle_vars = compute_bond_angle_variance(bond_network)

                # Check for anomalies (coordination > 6)
                for atom_idx, (coord, angle_var) in enumerate(zip(coord_nums, angle_vars)):
                    is_anomaly = coord > 6
                    if is_anomaly:
                        anomaly_count += 1
                        logger.debug(f"Atom {atom_idx} flagged as Physical Anomaly: coordination={coord}")

                    output_data.append({
                        "atom_id": atom_idx,
                        "coord_num": float(coord),
                        "angle_var": float(angle_var),
                        "is_valid": not is_anomaly,
                        "frame_id": frame_idx,
                        "system_size": len(atoms)
                    })

        else:
            # Standard loading for smaller files
            frames = stream.iread(
                str(trajectory_path),
                format=trajectory_path.suffix.strip('.')
            )

            if sample_limit:
                logger.info(f"Sampling limited to {sample_limit} frames.")
                sampling_info["used_sampling"] = True
                sampling_info["sample_size"] = sample_limit
                sampling_info["reason"] = "Explicit sample limit"
                frames = islice(frames, sample_limit)

            for frame_idx, atoms in enumerate(frames):
                processed_frames += 1
                total_atoms += len(atoms)

                # Determine cutoff
                if rdf_override:
                    cutoff = rdf_override
                else:
                    r, g_r = calculate_rdf(atoms, cutoff=5.0)
                    cutoff = determine_cutoff(r, g_r) if len(r) > 0 else 3.0

                if cutoff_used is None:
                    cutoff_used = cutoff

                # Construct bond network
                bond_network = construct_bond_network(atoms, cutoff)

                # Compute metrics
                coord_nums = compute_coordination_number(bond_network)
                angle_vars = compute_bond_angle_variance(bond_network)

                # Check for anomalies
                for atom_idx, (coord, angle_var) in enumerate(zip(coord_nums, angle_vars)):
                    is_anomaly = coord > 6
                    if is_anomaly:
                        anomaly_count += 1

                    output_data.append({
                        "atom_id": atom_idx,
                        "coord_num": float(coord),
                        "angle_var": float(angle_var),
                        "is_valid": not is_anomaly,
                        "frame_id": frame_idx,
                        "system_size": len(atoms)
                    })

        # Write output
        import csv
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=output_data[0].keys())
            writer.writeheader()
            writer.writerows(output_data)

        # Validate global coordination
        avg_coord = np.mean([d["coord_num"] for d in output_data])
        if abs(avg_coord - 4.0) > 0.05:
            logger.critical(f"CRITICAL: Acceptance Test Failed. Average coordination: {avg_coord:.3f} (expected ~4.0)")
            return_code = 3
        else:
            return_code = 0

        # Log sampling info if applicable
        if sampling_info["used_sampling"]:
            sampling_log_path = Path("data/metadata/sampling_log.txt")
            with open(sampling_log_path, 'w') as f:
                f.write(f"Sample Size: {sampling_info['sample_size']}\n")
                f.write(f"Reason: {sampling_info['reason']}\n")
                f.write(f"Total Frames Processed: {processed_frames}\n")
                f.write(f"Total Atoms Processed: {total_atoms}\n")
            logger.warning(f"Sampling used. See {sampling_log_path} for details.")

        logger.info(f"Extraction complete. Processed {processed_frames} frames, {total_atoms} atoms. "
                  f"Anomalies: {anomaly_count}. Cutoff used: {cutoff_used:.3f} Å")

        return {
            "status": "success",
            "frames_processed": processed_frames,
            "total_atoms": total_atoms,
            "anomalies_flagged": anomaly_count,
            "cutoff_used": cutoff_used,
            "avg_coordination": float(avg_coord),
            "return_code": return_code,
            "sampling_info": sampling_info
        }

    except Exception as e:
        logger.error(f"Fatal error during extraction: {str(e)}")
        raise

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract topology from MD trajectory")
    parser.add_argument("--input", required=True, help="Input trajectory file path")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--rdf-cutoff-override", type=float, default=None,
                      help="Override RDF cutoff (default: auto-detect)")
    parser.add_argument("--sample-limit", type=int, default=None,
                      help="Limit number of frames to process (for large files)")

    args = parser.parse_args()

    result = extract_topology(
        trajectory_path=Path(args.input),
        output_path=Path(args.output),
        rdf_override=args.rdf_cutoff_override,
        sample_limit=args.sample_limit
    )

    if result["return_code"] != 0:
        exit(result["return_code"])
    else:
        print(f"Topology extraction successful. Output written to {args.output}")

if __name__ == "__main__":
    main()
