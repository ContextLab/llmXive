import logging
import csv
from typing import List, Dict, Any, Optional
import requests
from pathlib import Path
import pandas as pd
from src.config import DATA_PROCESSED_PATH
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Ensembl Compara v109 API endpoint
ENSMBL_COMPARA_URL = "https://rest.ensembl.org/compara/synteny/region/human/"

def map_isg_genes(species: str, gene_list: List[str]) -> List[str]:
    """
    Map human ISG set to orthologs for non-human species using Ensembl Compara v109.

    Args:
        species: Target species name (e.g., 'mouse', 'rat', 'pig').
        gene_list: List of human gene symbols or Ensembl IDs to map.

    Returns:
        List of orthologous Ensembl IDs for the target species.
        If mapping fails for a specific gene, it is excluded from the result
        and logged. The function does NOT abort globally.

    Raises:
        ValueError: If species is 'human' (no mapping needed) or invalid format.
    """
    if species.lower() == 'human':
        logger.warning("Species is human. No ortholog mapping required. Returning original gene list.")
        return gene_list

    if not gene_list:
        logger.warning("Empty gene list provided. Returning empty list.")
        return []

    ortholog_map = []
    failed_genes = []

    headers = {"Content-Type": "application/json"}

    for gene in gene_list:
        try:
            # Construct the endpoint URL
            # Format: /compara/synteny/region/{species}/{region}
            # We use a generic region query or specific gene lookup if ID is provided.
            # For robustness, we attempt to look up the ortholog directly via the gene ID.
            # Ensembl API endpoint for orthologs: /homology/id/{id}
            # However, the task specifies Compara v109. Let's use the homology endpoint
            # which is part of Compara.
            
            # Using the homology endpoint which is more direct for gene-to-gene mapping
            homology_url = f"https://rest.ensembl.org/homology/id/{gene}"
            params = {"species": species, "type": "ortholog"}
            
            # Fallback to the specific Compara region endpoint if homology fails or for region-based logic
            # But homology/id is the standard way to get orthologs for a specific ID.
            
            # Let's try the homology endpoint first.
            # Note: If 'gene' is a symbol, we might need to map to ID first. 
            # For this implementation, we assume gene_list contains Ensembl IDs or 
            # symbols that the API can resolve if we use the correct endpoint.
            # The task says "map human ISG set". Usually ISG sets are defined by symbols or IDs.
            # We will assume Ensembl IDs for stability, or attempt to resolve symbols via /lookup.
            
            # Strategy: 
            # 1. If gene looks like an ID (starts with ENSG), use /homology/id/{gene}
            # 2. If it's a symbol, use /lookup/{symbol} to get ID, then /homology/id/{id}
            
            target_id = gene
            if not gene.startswith('ENSG'):
                # Try to resolve symbol to ID
                lookup_url = f"https://rest.ensembl.org/lookup/symbol/human/{gene}"
                lookup_resp = requests.get(lookup_url, headers=headers, timeout=10)
                if lookup_resp.status_code == 200:
                    target_id = lookup_resp.json().get('id')
                else:
                    logger.warning(f"Could not resolve symbol {gene} to ID. Skipping.")
                    failed_genes.append(gene)
                    continue

            if not target_id:
                logger.warning(f"Failed to resolve ID for {gene}. Skipping.")
                failed_genes.append(gene)
                continue

            # Now query orthologs
            url = f"https://rest.ensembl.org/homology/id/{target_id}"
            params = {"species": species, "type": "ortholog"}
            
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            
            if resp.status_code != 200:
                logger.warning(f"API request failed for {gene} (status {resp.status_code}). Skipping.")
                failed_genes.append(gene)
                continue

            data = resp.json()
            
            # Extract ortholog ID
            # Structure: {'data': [{'target': {'id': 'ENSMUSG000...'}}]}
            if 'data' in data and len(data['data']) > 0:
                homology_entry = data['data'][0]
                # Find the ortholog for the target species
                for hom in homology_entry.get('homologies', []):
                    if hom.get('target', {}).get('species') == species:
                        ortholog_id = hom['target']['id']
                        ortholog_map.append(ortholog_id)
                        break
                else:
                    # No ortholog found for this species
                    logger.warning(f"No ortholog found for {gene} in {species}. Skipping.")
                    failed_genes.append(gene)
            else:
                logger.warning(f"No homology data returned for {gene}. Skipping.")
                failed_genes.append(gene)

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error mapping {gene}: {e}")
            failed_genes.append(gene)
        except Exception as e:
            logger.error(f"Unexpected error mapping {gene}: {e}")
            failed_genes.append(gene)

    if failed_genes:
        logger.info(f"Successfully mapped {len(ortholog_map)} genes. Failed to map {len(failed_genes)}: {failed_genes[:5]}...")
    
    return ortholog_map

def save_ortholog_mapping(mapping: Dict[str, List[str]], output_path: Optional[str] = None) -> str:
    """
    Saves the ortholog mapping to a CSV file.
    
    Args:
        mapping: Dict where key is human gene ID/symbol and value is list of ortholog IDs.
        output_path: Optional path to save the file. Defaults to data/processed/ortholog_map.csv.
        
    Returns:
        The path where the file was saved.
    """
    if output_path is None:
        output_path = Path(DATA_PROCESSED_PATH) / "ortholog_map.csv"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    for human_gene, orthologs in mapping.items():
        for orth in orthologs:
            rows.append({"human_gene": human_gene, "ortholog_id": orth})
    
    df = pd.DataFrame(rows)
    if not df.empty:
        df.to_csv(output_path, index=False)
        logger.info(f"Ortholog mapping saved to {output_path}")
    else:
        logger.warning("No mappings to save. Creating empty file.")
        df.to_csv(output_path, index=False)
        
    return str(output_path)

def process_isg_mapping_for_species(species: str, isg_genes: List[str]) -> List[str]:
    """
    Wrapper to map ISG genes for a specific species and return the list of orthologs.
    Handles the 'response_unknown' logic by excluding unmapped genes from the list
    but logging the event.
    
    Args:
        species: Target species.
        isg_genes: List of human ISG genes.
        
    Returns:
        List of mapped ortholog Ensembl IDs.
    """
    mapped_genes = map_isg_genes(species, isg_genes)
    
    if not mapped_genes:
        logger.error(f"CRITICAL: No orthologs found for species {species}. ISG calculation will be skipped for this sample.")
        # We do NOT abort globally, but we return empty list which downstream should handle
        # by marking response_unknown.
    
    return mapped_genes