"""
save_networks.py

This script iterates over all CIF files in the supplied input directory,
constructs an atomic network graph for each material using the existing
network construction utilities, and saves the resulting NetworkX graph
as a pickle file in the specified output directory.

The output filename follows the convention ``<material_id>.pkl`` where
``material_id`` is derived from the CIF filename (the part before the
first dot).  The script logs progress and any errors encountered.
"""

import argparse
import logging
import pickle
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from pymatgen.core import Structure
from construct_network import construct_network_from_structure

def parse_arguments() -> argparse.Namespace:
    """Parse command‑line arguments."""
    parser = argparse.ArgumentParser(
        description="Construct atomic network graphs from CIF files and save them as pickles."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Directory containing CIF files (e.g., data/raw/cif/).",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Directory to write pickle files (e.g., data/processed/networks/).",
    )
    return parser.parse_args()

def setup_script_logger() -> logging.Logger:
    """Configure a logger for this script."""
    # Use the shared toolkit logger with a script‑specific name.
    return get_logger(__name__)

def material_id_from_path(cif_path: Path) -> str:
    """
    Derive a material identifier from the CIF filename.

    Expected filename pattern: ``<material_id>.cif`` (or any extension).
    The identifier is the stem of the file (everything before the first
    period).  This matches the convention used elsewhere in the project.
    """
    return cif_path.stem

def load_structure(cif_path: Path) -> Structure:
    """
    Load a pymatgen Structure from a CIF file.

    Parameters
    ----------
    cif_path : Path
        Path to the CIF file.

    Returns
    -------
    Structure
        The parsed crystal structure.
    """
    return Structure.from_file(str(cif_path))

def save_graph_pickle(graph, output_path: Path) -> None:
    """
    Serialize a NetworkX graph to a pickle file.

    Parameters
    ----------
    graph : networkx.Graph
        The graph to serialize.
    output_path : Path
        Destination file path (including ``.pkl`` suffix).
    """
    with output_path.open("wb") as f:
        pickle.dump(graph, f)

def main() -> None:
    """Entry point for the script."""
    args = parse_arguments()
    logger = setup_script_logger()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    # Ensure the output directory exists (paths helper creates parents).
    # Using the toolkit to keep path handling consistent.
    paths.path(output_dir)  # creates the directory if missing

    if not input_dir.is_dir():
        logger.error("Input directory does not exist: %s", input_dir)
        raise RuntimeError(f"Input directory not found: {input_dir}")

    cif_files = sorted(input_dir.glob("*.cif"))
    if not cif_files:
        logger.warning("No CIF files found in %s", input_dir)
        return

    processed_count = 0
    for cif_path in cif_files:
        try:
            material_id = material_id_from_path(cif_path)
            logger.info("Processing material %s from %s", material_id, cif_path.name)

            # Load the crystal structure.
            structure = load_structure(cif_path)

            # Build the network graph using the shared utility.
            graph, status, details = construct_network_from_structure(structure, logger)

            if graph is None:
                logger.warning(
                    "Graph construction failed for %s (status: %s, details: %s). Skipping.",
                    material_id,
                    status,
                    details,
                )
                continue

            # Determine output pickle path.
            pickle_path = output_dir / f"{material_id}.pkl"

            # Serialize the graph.
            save_graph_pickle(graph, pickle_path)
            logger.info("Saved graph for %s to %s", material_id, pickle_path)

            processed_count += 1

        except Exception as exc:
            logger.exception(
                "Unexpected error while processing %s: %s", cif_path.name, exc
            )
            # Continue with the next file; a single failure must not halt the whole run.

    logger.info("Finished processing CIFs. Successfully saved %d graph(s).", processed_count)

if __name__ == "__main__":
    main()
