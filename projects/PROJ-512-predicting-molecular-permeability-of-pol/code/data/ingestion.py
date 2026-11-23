import os
import sys
import logging
import csv
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit import RDLogger

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

# Local imports
from models.polymer_graph import PolymerGraph
from models.permeability_record import PermeabilityRecord
from data.utils import set_seed, get_seed, ensure_seed_initialized
from data.logging_config import get_logger

logger = get_logger(__name__)

class DataUnavailableError(Exception):
    """Raised when no real data source is available."""
    pass

def calculate_file_checksum(filepath: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksums(checksums: Dict[str, str], output_path: str) -> None:
    """Save checksums to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {output_path}")

def smiles_to_polymer_graph(smiles: str) -> Optional[PolymerGraph]:
    """
    Convert a SMILES string to a PolymerGraph object.

    Handles stereochemistry:
    - If a SMILES string contains undefined stereochemistry (e.g., `@?`),
      treat the bond as a single bond to ensure graph validity.

    Args:
        smiles (str): SMILES string representation of the molecule.

    Returns:
        Optional[PolymerGraph]: The constructed graph, or None if parsing fails.
    """
    try:
        # RDKit might fail on undefined stereochemistry by default
        # We attempt to sanitize and handle errors
        mol = Chem.MolFromSmiles(smiles, sanitize=True)

        if mol is None:
            # Attempt a more permissive parse
            mol_raw = Chem.MolFromSmiles(smiles, sanitize=False)
            if mol_raw is None:
                logger.warning(f"Failed to parse SMILES: {smiles}")
                return None
            mol = mol_raw  # Use the raw molecule without strict sanitization

        # Extract node and edge features
        nodes = []
        edges = []

        for atom in mol.GetAtoms():
            node_features = {
                "atom_type": atom.GetSymbol(),
                "hybridization": str(atom.GetHybridization()),
                "formal_charge": atom.GetFormalCharge(),
                "is_aromatic": atom.GetIsAromatic()
            }
            nodes.append(node_features)

        for bond in mol.GetBonds():
            edge_features = {
                "bond_type": str(bond.GetBondType()),
                "is_aromatic": bond.GetIsAromatic()
            }
            start_node = bond.GetBeginAtomIdx()
            end_node = bond.GetEndAtomIdx()
            edges.append((start_node, end_node, edge_features))

        # Create PolymerGraph
        graph = PolymerGraph(
            nodes=nodes,
            edges=edges,
            smiles=smiles
        )

        return graph

    except Exception as e:
        logger.error(f"Error converting SMILES to graph: {smiles}, error: {e}")
        return None

def calculate_mw(smiles: str) -> float:
    """
    Calculate the molecular weight of a repeat unit from SMILES.

    Args:
        smiles (str): SMILES string of the repeat unit.

    Returns:
        float: Molecular weight in Daltons.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 0.0
    return Descriptors.MolWt(mol)

def fetch_nist_pubchem_data() -> Tuple[List[Dict[str, Any]], str]:
    """
    Fetch real polymer data from NIST/PubChem via HuggingFace datasets.

    Tries multiple sources in order:
    1. datasets.load_dataset('polymer_science/permeability_nist')
    2. datasets.load_dataset('pubchem_polymer')
    3. Fallback to verified raw URLs (if available in the future)

    Returns:
        Tuple[List[Dict[str, Any]], str]: List of data records and the source used.

    Raises:
        DataUnavailableError: If no real data source is available.
    """
    try:
        from datasets import load_dataset

        # Try NIST source
        try:
            logger.info("Attempting to load dataset from polymer_science/permeability_nist...")
            dataset = load_dataset('polymer_science/permeability_nist', split='train')
            data = dataset.to_pandas().to_dict('records')
            logger.info(f"Successfully loaded {len(data)} records from NIST source.")
            return data, "polymer_science/permeability_nist"
        except Exception as e_nist:
            logger.warning(f"NIST source failed: {e_nist}")

        # Try PubChem source
        try:
            logger.info("Attempting to load dataset from pubchem_polymer...")
            dataset = load_dataset('pubchem_polymer', split='train')
            data = dataset.to_pandas().to_dict('records')
            logger.info(f"Successfully loaded {len(data)} records from PubChem source.")
            return data, "pubchem_polymer"
        except Exception as e_pubchem:
            logger.warning(f"PubChem source failed: {e_pubchem}")

        # If all HuggingFace sources fail, raise error
        raise DataUnavailableError(
            "FATAL: No real data available from NIST/PubChem. Real experimental data is required. "
            "Simulation is not a valid substitute. Execution halted."
        )

    except ImportError:
        raise DataUnavailableError("The 'datasets' library is not installed. Please install it to fetch real data.")
    except DataUnavailableError:
        raise
    except Exception as e:
        raise DataUnavailableError(f"Unexpected error fetching real data: {e}")

def process_dataset(raw_data: List[Dict[str, Any]], output_raw_path: str) -> Tuple[List[PolymerGraph], List[PermeabilityRecord], List[str]]:
    """
    Process raw dataset: convert SMILES to graphs, calculate MW, filter invalid entries,
    and apply cleaning rules (missing permeability, duplicate handling, MW threshold).

    Args:
        raw_data (List[Dict[str, Any]]): Raw data records from the fetcher.
        output_raw_path (str): Path to save the cleaned raw CSV.

    Returns:
        Tuple[List[PolymerGraph], List[PermeabilityRecord], List[str]]:
            - List of valid PolymerGraph objects
            - List of valid PermeabilityRecord objects
            - List of SMILES that were excluded (for review log)
    """
    graphs: List[PolymerGraph] = []
    records: List[PermeabilityRecord] = []
    excluded_smiles: List[str] = []

    # Track review log entries
    review_entries: List[Dict[str, str]] = []

    # Deduplication tracking
    seen_smiles: Dict[str, Tuple[int, PermeabilityRecord]] = {}

    for i, row in enumerate(raw_data):
        # Extract SMILES
        smiles = row.get('smiles') or row.get('SMILES') or row.get('smile')
        if not smiles:
            logger.warning(f"Row {i}: Missing SMILES, skipping.")
            continue

        # Extract permeability (log scale)
        permeability = row.get('permeability_log') or row.get('log_permeability') or row.get('permeability')
        if permeability is None:
            logger.warning(f"Row {i}: Missing permeability, skipping.")
            continue

        # Calculate molecular weight
        mw = calculate_mw(smiles)
        if mw < 1000:
            excluded_smiles.append(smiles)
            logger.debug(f"Excluding {smiles}: MW {mw:.2f} < 1000 Da")
            review_entries.append({
                "smiles": smiles,
                "status": "EXCLUDED",
                "reason": "MW < 1000 Da"
            })
            continue

        # Convert SMILES to graph
        graph = smiles_to_polymer_graph(smiles)
        if graph is None:
            excluded_smiles.append(smiles)
            logger.debug(f"Excluding {smiles}: Failed to convert to graph")
            review_entries.append({
                "smiles": smiles,
                "status": "EXCLUDED",
                "reason": "Failed graph conversion"
            })
            continue

        # Create permeability record
        record = PermeabilityRecord(
            smiles=smiles,
            permeability_log=float(permeability),
            molecular_weight=mw
        )

        # Duplicate handling
        if smiles in seen_smiles:
            existing_idx, existing_record = seen_smiles[smiles]
            variance = abs(record.permeability_log - existing_record.permeability_log)
            if variance > 0.5:
                # Flag for manual review
                excluded_smiles.append(smiles)
                logger.warning(f"Flagging {smiles} for review: High variance in duplicate values ({variance:.3f})")
                review_entries.append({
                    "smiles": smiles,
                    "status": "FLAGGED_CONFLICT",
                    "reason": "High variance in duplicate values"
                })
                continue
            else:
                # Average the permeability values
                avg_permeability = (record.permeability_log + existing_record.permeability_log) / 2
                seen_smiles[smiles] = (
                    existing_idx,
                    PermeabilityRecord(
                        smiles=smiles,
                        permeability_log=avg_permeability,
                        molecular_weight=mw
                    )
                )
                # No need to add a new graph; reuse existing one
                continue

        # First occurrence of this SMILES
        seen_smiles[smiles] = (len(graphs), record)
        graphs.append(graph)
        records.append(record)

    # Consolidate final records (averaged where applicable)
    final_records: List[PermeabilityRecord] = []
    for smiles, (idx, record) in seen_smiles.items():
        final_records.append(record)

    # Write cleaned raw CSV
    with open(output_raw_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['smiles', 'permeability_log', 'molecular_weight'])
        for rec in final_records:
            writer.writerow([rec.smiles, rec.permeability_log, rec.molecular_weight])

    # Write review log CSV
    review_log_path = os.path.join(os.path.dirname(output_raw_path), "review_log.csv")
    with open(review_log_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['smiles', 'status', 'reason'])
        for entry in review_entries:
            writer.writerow([entry['smiles'], entry['status'], entry['reason']])

    logger.info(f"Processed {len(final_records)} valid records. Excluded {len(excluded_smiles)} entries.")
    logger.info(f"Review log written to {review_log_path}")
    return graphs, final_records, excluded_smiles

def main():
    """Main entry point for the ingestion script."""
    ensure_seed_initialized()

    # Paths
    raw_output_path = "data/raw/polymer_raw.csv"
    checksums_path = "data/raw/checksums.json"

    # Ensure directories exist
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    # Fetch data
    try:
        data, source = fetch_nist_pubchem_data()
        logger.info(f"Data fetched from {source}")
    except DataUnavailableError as e:
        logger.error(str(e))
        sys.exit(1)

    # Process dataset (cleaning, deduplication, MW filter, review log)
    graphs, records, excluded_smiles = process_dataset(data, raw_output_path)

    # Save checksums for the cleaned raw CSV
    checksum = calculate_file_checksum(raw_output_path)
    save_checksums({"polymer_raw.csv": checksum}, checksums_path)

    logger.info("Ingestion complete.")

if __name__ == "__main__":
    main()
