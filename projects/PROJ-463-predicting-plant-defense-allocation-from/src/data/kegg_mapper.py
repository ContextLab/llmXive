"""
KEGG/GO Pathway Mapping Module (T036).

Fetches pathway mappings for genes using the bioservices KEGG interface or
a local static fallback file. Outputs a JSON manifest at
`data/processed/pathway_mappings.json`.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Attempt to import bioservices; if not available, we rely on the local fallback
try:
    from bioservices import KEGG
    BIOSERVICES_AVAILABLE = True
except ImportError:
    BIOSERVICES_AVAILABLE = False
    logging.warning("bioservices not installed. Falling back to local KEGG mapping.")

from src.utils.logger import get_logger
from src.utils.config import get_data_path

logger = get_logger(__name__)

# Constants
LOCAL_MAPPING_PATH = "data/raw/kegg_mapping_local.json"
OUTPUT_PATH = "data/processed/pathway_mappings.json"


def load_local_mapping() -> Dict[str, Any]:
    """
    Load the local static KEGG mapping file.
    Returns an empty dict if the file does not exist.
    """
    data_root = get_data_path()
    local_file = data_root / LOCAL_MAPPING_PATH

    if not local_file.exists():
        logger.warning(f"Local mapping file not found at {local_file}. Returning empty mapping.")
        return {}

    try:
        with open(local_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse local mapping file {local_file}: {e}")
        return {}


def fetch_kegg_mappings_api(gene_ids: List[str], organism: str = "ath") -> Dict[str, List[str]]:
    """
    Fetch KEGG pathway mappings for a list of gene IDs using bioservices.

    Args:
        gene_ids: List of gene identifiers (e.g., AT1G01010).
        organism: KEGG organism code (default: 'ath' for Arabidopsis thaliana).

    Returns:
        Dict mapping gene_id -> list of pathway IDs (koXXXXX).
    """
    if not BIOSERVICES_AVAILABLE:
        raise ImportError("bioservices library is required for API fetching but is not installed.")

    k = KEGG()
    mappings: Dict[str, List[str]] = {}
    batch_size = 100  # KEGG API often has limits on batch sizes

    for i in range(0, len(gene_ids), batch_size):
        batch = gene_ids[i : i + batch_size]
        batch_str = "+".join(batch)

        try:
            # Convert gene ID to pathway mapping
            # KEGG API: /link/pathway/{organism}:{gene_id}
            # bioservices.link handles this
            result = k.link("pathway", f"{organism}:{batch_str}")

            if result:
                # Parse the result. bioservices.link returns a list of dicts or a string depending on version
                # Typically: [{'id': 'ath:AT1G01010', 'description': 'ko00010', ...}]
                # We need to map gene -> pathways
                for entry in result:
                    gene_id = entry.get("id", "").replace(f"{organism}:", "")
                    pathway = entry.get("description", "") # e.g., "ko00010"
                    if gene_id and pathway:
                        if gene_id not in mappings:
                            mappings[gene_id] = []
                        if pathway not in mappings[gene_id]:
                            mappings[gene_id].append(pathway)
        except Exception as e:
            logger.error(f"Failed to fetch mappings for batch {batch}: {e}")
            # Continue with next batch

    return mappings


def get_unique_genes_from_processed_data() -> List[str]:
    """
    Scans the processed directory for count matrices or DE results to identify
    the set of unique gene IDs that need mapping.
    """
    data_root = get_data_path()
    processed_dir = data_root / "processed"
    gene_ids = set()

    # Look for count matrices or DE result files
    # Assuming T012c produced {accession_id}_tpm.csv or similar
    # And T018 produced DE results
    # We'll scan for CSVs in processed/count_matrices or processed/
    for pattern in ["**/*.csv", "**/*.tsv"]:
        for file_path in processed_dir.glob(pattern):
            try:
                # Heuristic: First column is usually gene_id
                with open(file_path, "r", encoding="utf-8") as f:
                    header = f.readline().strip().split(",")[0]
                    # Simple check: if first row looks like a gene ID (starts with AT or similar)
                    # This is a rough heuristic for demonstration
                    for line in f:
                        parts = line.strip().split(",")
                        if parts and len(parts) > 0:
                            gid = parts[0]
                            if gid and not gid.startswith("gene") and not gid.startswith("Gene"):
                                gene_ids.add(gid)
            except Exception as e:
                logger.debug(f"Could not parse {file_path} for gene IDs: {e}")

    return list(gene_ids)


def main():
    """
    Main entry point for T036.
    1. Determine the set of genes to map (from processed data).
    2. Attempt to fetch from KEGG API (bioservices).
    3. If API fails or unavailable, load local fallback.
    4. Merge results (API takes precedence).
    5. Write output to data/processed/pathway_mappings.json.
    """
    logger.info("Starting KEGG Pathway Mapping (T036)...")

    # 1. Identify genes
    all_genes = get_unique_genes_from_processed_data()
    if not all_genes:
        logger.warning("No gene IDs found in processed data. Creating empty mapping.")
        all_genes = [] # Proceed with empty if no data found

    logger.info(f"Found {len(all_genes)} unique gene IDs to map.")

    final_mappings: Dict[str, List[str]] = {}
    source_used = "local"

    # 2. Attempt API fetch
    if BIOSERVICES_AVAILABLE and all_genes:
        logger.info("Attempting to fetch KEGG mappings via bioservices...")
        try:
            # Defaulting to 'ath' (Arabidopsis) as per common context in this project
            # In a real multi-species scenario, we would need species-specific codes
            api_mappings = fetch_kegg_mappings_api(all_genes, organism="ath")
            if api_mappings:
                final_mappings = api_mappings
                source_used = "api"
                logger.info(f"Successfully fetched {len(final_mappings)} gene mappings from KEGG API.")
            else:
                logger.warning("API returned no mappings. Falling back to local file.")
        except Exception as e:
            logger.error(f"KEGG API fetch failed: {e}. Falling back to local file.")
    else:
        if not BIOSERVICES_AVAILABLE:
            logger.info("bioservices not available. Using local fallback.")
        elif not all_genes:
            logger.info("No genes to map. Using local fallback (empty).")

    # 3. Fallback / Merge with local
    if not final_mappings:
        local_mappings = load_local_mapping()
        if local_mappings:
            final_mappings = local_mappings
            source_used = "local"
            logger.info(f"Loaded {len(final_mappings)} mappings from local file.")
        else:
            logger.warning("No mappings found in local file either.")

    # 4. Write Output
    data_root = get_data_path()
    output_file = data_root / OUTPUT_PATH
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "source": source_used,
        "total_genes_mapped": len(final_mappings),
        "mappings": final_mappings
    }

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Pathway mappings written to {output_file}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        sys.exit(1)

    return output_data


if __name__ == "__main__":
    main()
