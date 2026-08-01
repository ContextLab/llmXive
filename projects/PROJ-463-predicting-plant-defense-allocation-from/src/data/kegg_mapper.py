"""
KEGG/GO Pathway Mapping Module.

Fetches pathway mappings for genes using bioservices or direct REST API.
Falls back to a local static mapping file if the API is unavailable.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Try to import bioservices, but handle if it's not installed
try:
    from bioservices import KEGG
    BIOSERVICES_AVAILABLE = True
except ImportError:
    BIOSERVICES_AVAILABLE = False
    logging.getLogger(__name__).warning(
        "bioservices not installed. Will rely on local fallback or direct API if possible."
    )

import requests

from src.utils.logger import get_logger
from src.utils.config import get_data_path

logger = get_logger(__name__)


def load_local_fallback_mapping(fallback_path: Path) -> Dict[str, List[str]]:
    """
    Load the local static mapping file.

    Args:
        fallback_path: Path to data/raw/kegg_mapping_local.json

    Returns:
        Dictionary mapping gene_id to list of pathway IDs.
    """
    if not fallback_path.exists():
        logger.error(f"Local fallback file not found: {fallback_path}")
        return {}

    try:
        with open(fallback_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} gene mappings from local fallback.")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse local fallback JSON: {e}")
        return {}


def fetch_kegg_mappings_via_api(gene_ids: Optional[List[str]] = None) -> Dict[str, List[str]]:
    """
    Fetch KEGG pathway mappings using bioservices or direct REST API.

    Args:
        gene_ids: Optional list of specific gene IDs to fetch. If None, attempts to fetch all for the organism.

    Returns:
        Dictionary mapping gene_id to list of pathway IDs.
    """
    mappings = {}
    organism = "ath"  # Default to Arabidopsis thaliana as per project context
    kegg = None

    if BIOSERVICES_AVAILABLE:
        try:
            kegg = KEGG()
            logger.info("Using bioservices.KEGG for mapping.")
        except Exception as e:
            logger.warning(f"bioservices initialization failed: {e}. Falling back to direct API.")
            kegg = None

    # Strategy 1: Use bioservices if available and successful
    if kegg is not None:
        try:
            # If specific genes are requested, fetch them one by one or in a batch if supported
            # bioservices kegg.link and kegg.get are the main tools
            # For efficiency, we might fetch all genes for the organism and filter, or iterate.
            # Given the potential size, let's try to fetch a sample or the full list if small.
            # A robust way with bioservices is to list all genes for the organism then link.
            # However, kegg.list() might be heavy. Let's try direct mapping if gene_ids provided.
            
            if gene_ids:
                for gid in gene_ids:
                    # kegg.link returns pathway IDs linked to this gene
                    # Format: "path:ath00010" etc.
                    try:
                        links = kegg.link("path", gid)
                        if links:
                            # Parse the result string which looks like "path:ath00010\tath00010\n..."
                            # Actually kegg.link returns a string like "path:ath00010\tath00010"
                            # We need to extract the pathway ID part.
                            # The format is usually "database:entry_id\tdatabase:entry_id"
                            # Let's split by newline and extract the second part or just the path ID.
                            # bioservices returns a string.
                            lines = links.strip().split('\n')
                            pathway_ids = []
                            for line in lines:
                                if '\t' in line:
                                    parts = line.split('\t')
                                    # parts[0] is "path:athXXXXX", parts[1] is "athXXXXX" (or similar)
                                    # We want the full path string or just the ID? Schema says "koXXXXX" or "path:athXXXXX".
                                    # The task schema says: "pathways": ["koXXXXX"].
                                    # Let's store the full path string as found in the local file for consistency,
                                    # or normalize to the ID. The local file has "path:ath...".
                                    # Let's keep the "path:..." format if possible, or extract the ID.
                                    # The local file uses "path:ath00010".
                                    # bioservices link returns "path:ath00010\tath00010".
                                    # Let's extract the first part "path:ath00010".
                                    pathway_ids.append(parts[0])
                            if pathway_ids:
                                mappings[gid] = pathway_ids
                    except Exception as e:
                        logger.debug(f"Failed to fetch link for {gid}: {e}")
            else:
                # If no specific genes, we might need to list all genes for 'ath'
                # This can be large. Let's skip bulk fetch if no gene_ids provided and rely on fallback
                # or fetch a known set if needed later.
                logger.warning("No gene_ids provided for bulk fetch. Skipping bulk API fetch.")
        except Exception as e:
            logger.error(f"Error using bioservices: {e}")

    # Strategy 2: Direct REST API (KEGG API)
    # If bioservices failed or wasn't used, try direct requests.
    # KEGG API endpoint: http://rest.kegg.jp/link/pathway/{gene_id}
    # Returns: path:athXXXXX\tathXXXXX
    if not mappings and gene_ids:
        logger.info("Attempting direct KEGG REST API.")
        for gid in gene_ids:
            try:
                url = f"http://rest.kegg.jp/link/pathway/{organism}{gid}"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    lines = resp.text.strip().split('\n')
                    pathway_ids = []
                    for line in lines:
                        if '\t' in line:
                            parts = line.split('\t')
                            pathway_ids.append(parts[0]) # "path:athXXXXX"
                    if pathway_ids:
                        mappings[gid] = pathway_ids
            except Exception as e:
                logger.debug(f"Direct API failed for {gid}: {e}")

    # If still empty and we have gene_ids, we might have missed some.
    # If we have no gene_ids, we definitely can't fetch specific ones without a list.
    return mappings


def get_all_genes_from_expression_data() -> List[str]:
    """
    Scans data/processed for TPM/Count matrices to extract unique gene IDs.
    This ensures we map pathways for all genes present in the processed data.
    """
    processed_dir = get_data_path() / "processed"
    gene_ids = set()
    
    if not processed_dir.exists():
        logger.warning(f"Processed directory {processed_dir} does not exist. Cannot extract gene IDs.")
        return []

    # Look for CSV files that look like expression matrices
    for file_path in processed_dir.glob("*.csv"):
        try:
            # Assume first column is gene ID or index. 
            # We need to be careful. Let's assume a standard format: gene_id, sample1, sample2...
            # Or if it's a long format, it might differ.
            # Given the context of T012c output: {accession_id}_tpm.csv
            # These are likely wide matrices.
            import pandas as pd
            df = pd.read_csv(file_path)
            
            # Heuristic: If first column is not numeric, assume it's gene_id
            if df.columns[0] not in ['gene_id', 'GeneID', 'ID', 'Gene']:
                # Check if the first column looks like gene IDs (e.g., AT1G...)
                if df.iloc[0, 0].startswith('AT') or df.iloc[0, 0].startswith('ATG'):
                    gene_ids.update(df.iloc[:, 0].astype(str).tolist())
                else:
                    # Maybe it's an index? Try to infer.
                    # If the first column contains non-numeric strings, treat as gene IDs.
                    if not pd.api.types.is_numeric_dtype(df.iloc[:, 0]):
                        gene_ids.update(df.iloc[:, 0].astype(str).tolist())
            else:
                # Explicit gene_id column
                gene_ids.update(df['gene_id'].astype(str).tolist())
                
        except Exception as e:
            logger.debug(f"Could not parse {file_path} for gene IDs: {e}")
            continue

    logger.info(f"Extracted {len(gene_ids)} unique gene IDs from processed data.")
    return list(gene_ids)


def main():
    """
    Main entry point for KEGG Mapper.
    Fetches mappings and saves to data/processed/pathway_mappings.json.
    """
    logger.info("Starting KEGG Pathway Mapping...")
    
    data_path = get_data_path()
    output_path = data_path / "processed" / "pathway_mappings.json"
    fallback_path = data_path / "raw" / "kegg_mapping_local.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Get target gene IDs
    # We need to map pathways for genes present in our processed data.
    # If no processed data exists yet, we might fall back to a default set or the local file.
    gene_ids = get_all_genes_from_expression_data()
    
    if not gene_ids:
        logger.warning("No gene IDs found in processed data. Attempting to use all genes from local fallback.")
        # If we can't find genes, we might just load the local fallback as is, 
        # or try to fetch a general list. For now, we'll try to load local fallback directly.
        local_data = load_local_fallback_mapping(fallback_path)
        if local_data:
            mappings = local_data
            logger.info("Using local fallback as primary source due to missing gene list.")
        else:
            logger.error("No gene IDs found and no local fallback available.")
            mappings = {}
    else:
        # 2. Try API first
        mappings = fetch_kegg_mappings_via_api(gene_ids)
        
        # 3. If API returned nothing or partial, load local fallback and merge
        if not mappings:
            logger.warning("API fetch returned no mappings. Loading local fallback.")
            local_data = load_local_fallback_mapping(fallback_path)
            mappings = local_data
        else:
            # Merge with local fallback for any missing genes
            local_data = load_local_fallback_mapping(fallback_path)
            for gid, paths in local_data.items():
                if gid not in mappings:
                    mappings[gid] = paths
            logger.info("Merged API results with local fallback.")

    # 4. Validate and Save
    # Schema: { "gene_id": "string", "pathways": ["koXXXXX"] }
    # Our data structure is { "gene_id": ["path1", "path2", ...] }
    # We need to ensure it's a list of strings.
    
    final_output = {}
    for gid, paths in mappings.items():
        if isinstance(paths, list):
            final_output[gid] = paths
        elif isinstance(paths, str):
            final_output[gid] = [paths]
        else:
            logger.warning(f"Skipping invalid pathway data for {gid}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=2)
        logger.info(f"Successfully wrote pathway mappings to {output_path}")
        logger.info(f"Total genes mapped: {len(final_output)}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        sys.exit(1)

    return final_output


if __name__ == "__main__":
    main()
