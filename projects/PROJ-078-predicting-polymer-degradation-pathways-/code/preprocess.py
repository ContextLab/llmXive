"""
Preprocessing pipeline for polymer degradation data.

Handles SMILES canonicalization, molecular graph conversion,
environmental data filtering, polyester filtering, and dataset saving.
"""
import logging
import json
import hashlib
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Union

import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import pandas as pd

from utils import get_logger, get_project_paths
from data_models import PolymerRecord, MolecularGraph

logger = get_logger(__name__)
PATHS = get_project_paths()

# Ester functional group SMARTS pattern for polyester detection
# Matches the ester linkage: -C(=O)O-
ESTER_SMARTS = "C(=O)O"

def canonicalize_smiles(smiles: str) -> Optional[str]:
    """
    Convert a SMILES string to its canonical form.
    
    Args:
        smiles: Input SMILES string.
        
    Returns:
        Canonical SMILES string or None if invalid.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol, canonical=True)
    except Exception as e:
        logger.warning(f"Failed to canonicalize SMILES '{smiles}': {e}")
        return None

def smiles_to_molecular_graph(smiles: str) -> Optional[MolecularGraph]:
    """
    Convert a SMILES string to a MolecularGraph data object.
    
    Args:
        smiles: Canonical or non-canonical SMILES string.
        
    Returns:
        MolecularGraph object or None if conversion fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        # Add hydrogen atoms for complete graph representation
        mol = Chem.AddHs(mol)

        # Extract node features (atomic numbers)
        atomic_numbers = [atom.GetAtomicNum() for atom in mol.GetAtoms()]
        
        # Extract edge indices (bond connectivity)
        edge_list = []
        for bond in mol.GetBonds():
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()
            edge_list.append([i, j])
            edge_list.append([j, i])  # Undirected graph

        if not edge_list:
            # Handle single atom molecules
            edge_list = [[0, 0]]

        edge_indices = np.array(edge_list, dtype=np.int64).T
        
        return MolecularGraph(
            smiles=smiles,
            atomic_numbers=np.array(atomic_numbers, dtype=np.int64),
            edge_indices=edge_indices,
            num_atoms=len(atomic_numbers),
            num_bonds=len(mol.GetBonds())
        )
    except Exception as e:
        logger.warning(f"Failed to convert SMILES '{smiles}' to graph: {e}")
        return None

def filter_missing_environmental_data(
    records: List[PolymerRecord]
) -> Tuple[List[PolymerRecord], List[PolymerRecord]]:
    """
    Filter records that are missing required environmental data (temp, pH, UV).
    
    According to methodological correction: records with missing environmental
    data MUST be EXCLUDED to prevent confounding. Imputation is FORBIDDEN.
    
    Args:
        records: List of PolymerRecord objects.
        
    Returns:
        Tuple of (valid_records, excluded_records).
    """
    valid = []
    excluded = []
    
    for record in records:
        # Check if all required environmental parameters are present and non-null
        has_temp = record.temperature is not None
        has_ph = record.ph is not None
        has_uv = record.uv_intensity is not None
        
        if has_temp and has_ph and has_uv:
            valid.append(record)
        else:
            reasons = []
            if not has_temp: reasons.append("temperature")
            if not has_ph: reasons.append("pH")
            if not has_uv: reasons.append("UV intensity")
            excluded.append((record, reasons))
            
    logger.info(f"Environmental data filtering: {len(valid)} valid, {len(excluded)} excluded")
    for rec, reasons in excluded:
        logger.debug(f"Excluded record {rec.id}: missing {', '.join(reasons)}")
        
    return valid, excluded

def is_polyester(smiles: str) -> bool:
    """
    Check if a molecule contains ester functional groups.
    
    Args:
        smiles: SMILES string of the molecule.
        
    Returns:
        True if the molecule contains ester groups, False otherwise.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        
        ester_pattern = Chem.MolFromSmarts(ESTER_SMARTS)
        if ester_pattern is None:
            return False
            
        matches = mol.GetSubstructMatches(ester_pattern)
        return len(matches) > 0
    except Exception as e:
        logger.warning(f"Error checking polyester for SMILES '{smiles}': {e}")
        return False

def filter_polyesters(records: List[PolymerRecord]) -> Tuple[List[PolymerRecord], List[PolymerRecord]]:
    """
    Filter dataset to retain only polyesters based on functional group detection.
    
    Args:
        records: List of PolymerRecord objects.
        
    Returns:
        Tuple of (polyester_records, non_polyester_records).
    """
    polyesters = []
    non_polyesters = []
    
    for record in records:
        if is_polyester(record.smiles):
            polyesters.append(record)
        else:
            non_polyesters.append(record)
            
    logger.info(f"Polyester filtering: {len(polyesters)} retained, {len(non_polyesters)} excluded")
    
    # Generate filter report
    report_path = PATHS["processed"] / "polyester_filter_report.csv"
    report_df = pd.DataFrame([
        {
            "id": r.id,
            "smiles": r.smiles,
            "is_polyester": r in polyesters
        }
        for r in records
    ])
    report_df.to_csv(report_path, index=False)
    logger.info(f"Generated polyester filter report: {report_path}")
    
    return polyesters, non_polyesters

def apply_edge_dropout(
    graph: MolecularGraph,
    dropout_rate: float = 0.1,
    preserve_ester_bonds: bool = True
) -> MolecularGraph:
    """
    Apply functional-group-preserving edge dropout.
    
    Only non-ester bonds are eligible for dropout to preserve chemical validity.
    
    Args:
        graph: Input MolecularGraph.
        dropout_rate: Probability of dropping an edge.
        preserve_ester_bonds: If True, ester bonds are never dropped.
        
    Returns:
        Augmented MolecularGraph with some edges dropped.
    """
    # This is a placeholder for the actual implementation which would require
    # reconstructing the RDKit molecule to identify bond types.
    # For now, we return the original graph as the core task is data saving.
    # The augmentation logic is implemented in T022.
    return graph

def compute_checksum(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal checksum string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_dataset(
    records: List[PolymerRecord],
    output_dir: Union[str, Path],
  filename_prefix: str,
    include_checksums: bool = True
) -> Dict[str, Any]:
    """
    Save a list of PolymerRecord objects to CSV files with checksums.
    
    Args:
        records: List of PolymerRecord objects to save.
        output_dir: Directory path where files will be saved.
        filename_prefix: Prefix for output filenames (e.g., 'raw' or 'processed').
        include_checksums: Whether to compute and save checksums.
        
    Returns:
        Dictionary containing file paths and checksums.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Convert records to DataFrame
    data = []
    for r in records:
        data.append({
            "id": r.id,
            "smiles": r.smiles,
            "temperature": r.temperature,
            "ph": r.ph,
            "uv_intensity": r.uv_intensity,
            "degradation_pathway": r.degradation_pathway,
            "source": r.source,
            "num_atoms": r.num_atoms,
            "num_bonds": r.num_bonds
        })
    
    df = pd.DataFrame(data)
    csv_path = output_path / f"{filename_prefix}_dataset.csv"
    df.to_csv(csv_path, index=False)
    
    result = {
        "file_path": str(csv_path),
        "num_records": len(records),
        "columns": list(df.columns)
    }
    
    if include_checksums:
        checksum = compute_checksum(csv_path)
        result["checksum"] = checksum
        
        # Save checksum to a separate file
        checksum_path = output_path / f"{filename_prefix}_dataset.csv.sha256"
        with open(checksum_path, "w") as f:
            f.write(f"{checksum}  {csv_path.name}\n")
        result["checksum_file"] = str(checksum_path)
        
    logger.info(f"Saved {len(records)} records to {csv_path}")
    return result

def main():
    """
    Main entry point for the preprocessing pipeline.
    
    This function orchestrates the full preprocessing workflow:
    1. Load raw data (from T012/T013 output)
    2. Filter missing environmental data (T014b)
    3. Filter to polyesters (T015)
    4. Save raw and processed datasets with checksums (T016)
    """
    logger.info("Starting preprocessing pipeline (T016)")
    
    # Ensure directories exist
    raw_dir = PATHS["raw"]
    processed_dir = PATHS["processed"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Locate input raw data from previous steps
    # Expected input: data/raw/polyester_candidates.csv (from T015)
    input_file = raw_dir / "polyester_candidates.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T015 (polyester filtering) has been completed.")
        return
        
    # Load raw data
    logger.info(f"Loading raw data from {input_file}")
    try:
        df_raw = pd.read_csv(input_file)
        records = []
        for _, row in df_raw.iterrows():
            record = PolymerRecord(
                id=row["id"],
                smiles=row["smiles"],
                temperature=row.get("temperature"),
                ph=row.get("ph"),
                uv_intensity=row.get("uv_intensity"),
                degradation_pathway=row.get("degradation_pathway"),
                source=row.get("source", "unknown"),
                num_atoms=row.get("num_atoms"),
                num_bonds=row.get("num_bonds")
            )
            records.append(record)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        return

    logger.info(f"Loaded {len(records)} records")
    
    # Save raw dataset (after polyester filtering but before final exclusions)
    # This represents the "raw" state after initial filtering
    raw_result = save_dataset(
        records,
        raw_dir,
        "raw_filtered",
        include_checksums=True
    )
    logger.info(f"Raw dataset saved: {raw_result['file_path']}")
    
    # Step 1: Filter missing environmental data (T014b)
    valid_records, excluded_env = filter_missing_environmental_data(records)
    logger.info(f"Environmental filtering: {len(excluded_env)} records excluded")
    
    # Step 2: Save processed dataset (final training set)
    processed_result = save_dataset(
        valid_records,
        processed_dir,
        "processed_training",
        include_checksums=True
    )
    logger.info(f"Processed dataset saved: {processed_result['file_path']}")
    
    # Log summary
    logger.info("Preprocessing pipeline completed successfully")
    logger.info(f"Raw dataset: {raw_result['file_path']} (checksum: {raw_result.get('checksum', 'N/A')})")
    logger.info(f"Processed dataset: {processed_result['file_path']} (checksum: {processed_result.get('checksum', 'N/A')})")
    logger.info(f"Total records excluded due to missing env data: {len(excluded_env)}")

if __name__ == "__main__":
    main()
