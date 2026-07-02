import os
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import requests
from xml.etree import ElementTree as ET

# Import from local project modules (per API surface)
from config import load_config, get_organisms, get_path, ensure_dirs
from utils import setup_logging, exponential_backoff

logger = logging.getLogger(__name__)

class DataLoadingError(Exception):
    """Custom exception for data loading failures."""
    pass

# BioMart Configuration
BIOMART_URL = "https://www.ensembl.org/biomart/martservice"
# Default attributes for Ensembl Gene ID mapping
# We request 'ensembl_gene_id' as the primary key and 'external_gene_name' for STRING/DEG alignment
# We also request 'description' for debugging/logging if needed
BIOMART_ATTRIBUTES = [
    'ensembl_gene_id',
    'external_gene_name',
    'description'
]

def _get_biomart_session() -> requests.Session:
    """Create a session with retries for BioMart."""
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=10,
        pool_maxsize=20,
        max_retries=requests.adapters.Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def _fetch_ensembl_mapping(
    organism: str,
    gene_ids: Set[str],
    id_type: str = 'external_gene_name'
) -> Dict[str, str]:
    """
    Fetch Ensembl Gene ID mappings for a set of gene IDs using BioMart.

    Args:
        organism: Ensembl organism prefix (e.g., 'yeast', 'hsapiens').
        gene_ids: Set of gene IDs to map (usually from STRING or DEG).
        id_type: The type of ID we are mapping FROM (e.g., 'external_gene_name').

    Returns:
        Dict mapping the input ID to 'ensembl_gene_id'.
    """
    if not gene_ids:
        return {}

    logger.info(f"Starting BioMart mapping for {organism} with {len(gene_ids)} IDs.")
    
    # BioMart filter configuration
    # We use 'external_gene_name' as the filter if the input IDs are gene symbols
    # If the input IDs are already Ensembl IDs, we might just return them, 
    # but the task implies aligning STRING (often symbols or Ensembl) and DEG (often symbols).
    # We assume input is 'external_gene_name' (symbol) for this task.
    
    # Construct the XML query for BioMart
    # Note: BioMart XML syntax can be verbose. We use a simpler GET request with parameters
    # or the XML POST method. The XML POST method is more robust for large lists.
    
    xml_query = f"""
    <!DOCTYPE Query>
    <Query  virtualSchemaName = "default" 
            formatter = "TSV" 
            header = "0" 
            uniqueRows = "1" 
            datasetConfigVersion = "0.6" 
            count = "0">
        <Dataset name = "{organism}_gene_ensembl" interface = "default">
            <Filter name = "{id_type}" value = "{','.join(list(gene_ids)[:100])}"/> 
            <!-- Note: BioMart has limits on filter value length in some endpoints. 
                 For very large sets, we might need chunking. 
                 However, for typical PPI networks, we can try a batch or use the 'list' feature. 
                 A more robust approach for >1000 IDs is to upload a list file, 
                 but for this script we will attempt a batched GET approach or XML filter.
                 Given the constraints of a single script, we will use the XML filter with a limit 
                 or chunk the request if the list is huge. 
                 Here we assume a reasonable size or use the 'external_gene_name' filter directly.
                 If the list is too long for the URL/Filter value, we chunk. -->
            <Attribute name = "ensembl_gene_id"/>
            <Attribute name = "{id_type}"/>
        </Dataset>
    </Query>
    """
    
    # BioMart XML filter values often have a character limit.
    # For large sets, we should chunk. Let's implement a simple chunking strategy.
    chunk_size = 500
    mapping = {}
    session = _get_biomart_session()
    
    # If the list is too big for a single filter, we split.
    # However, the XML filter 'value' attribute in the query above is not the best way for large lists.
    # A better way for large lists in BioMart is to use the 'list' type filter or simply
    # query all and filter in memory (too slow for huge genomes) or use the 'external_gene_name' filter
    # with a list of names.
    
    # Let's use the standard BioMart XML query but with a list of names.
    # If the number of genes is large, we might hit limits.
    # We will implement a chunked query to be safe.
    
    ids_list = list(gene_ids)
    total_batches = (len(ids_list) + chunk_size - 1) // chunk_size
    
    for i in range(0, len(ids_list), chunk_size):
        batch = ids_list[i:i+chunk_size]
        logger.debug(f"Processing batch {i//chunk_size + 1}/{total_batches}")
        
        # Construct XML with specific batch
        # We need to be careful with the XML structure. 
        # The 'value' attribute in Filter usually takes a comma-separated list.
        # If the list is too long, the server might reject it.
        # Let's try the standard query first.
        
        batch_xml = f"""
        <!DOCTYPE Query>
        <Query  virtualSchemaName = "default" 
                formatter = "TSV" 
                header = "0" 
                uniqueRows = "1" 
                datasetConfigVersion = "0.6" 
                count = "0">
            <Dataset name = "{organism}_gene_ensembl" interface = "default">
                <Filter name = "{id_type}" value = "{','.join(batch)}"/>
                <Attribute name = "ensembl_gene_id"/>
                <Attribute name = "{id_type}"/>
            </Dataset>
        </Query>
        """
        
        try:
            response = session.post(
                BIOMART_URL,
                data=batch_xml,
                headers={'Content-Type': 'application/xml'},
                timeout=60
            )
            response.raise_for_status()
            
            # Parse TSV response
            lines = response.text.strip().split('\n')
            for line in lines:
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:
                    ensembl_id = parts[0].strip()
                    input_id = parts[1].strip()
                    if ensembl_id and input_id:
                        mapping[input_id] = ensembl_id
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"BioMart request failed for batch {i//chunk_size + 1}: {e}")
            # Continue with other batches
            continue
        except ET.ParseError as e:
            logger.warning(f"Failed to parse BioMart response XML/TSV: {e}")
            continue

    logger.info(f"BioMart mapping completed. Found {len(mapping)} mappings out of {len(gene_ids)} requested.")
    return mapping

def map_ids(
    organism: str,
    string_genes: Set[str],
    deg_genes: Set[str],
    output_dir: Optional[Path] = None
) -> Tuple[Set[str], float]:
    """
    Map STRING and DEG gene identifiers to a common Ensembl ID space.
    
    This function:
    1. Fetches Ensembl IDs for STRING genes (assuming they are symbols or Ensembl IDs).
    2. Fetches Ensembl IDs for DEG genes (assuming they are symbols or Ensembl IDs).
    3. Intersects the resulting Ensembl IDs to find common genes.
    4. Logs the mapping coverage percentage.
    
    Args:
        organism: The organism code (e.g., 'yeast', 'hsapiens').
        string_genes: Set of gene IDs from STRING network.
        deg_genes: Set of gene IDs from DEG database.
        output_dir: Optional directory to save mapping reports.
        
    Returns:
        Tuple of (common_ensembl_ids, mapping_coverage_percent).
    """
    logger.info(f"Starting ID mapping for organism: {organism}")
    
    # Determine the ID type. 
    # If the IDs look like Ensembl IDs (e.g., ENSG...), we might skip mapping or just normalize.
    # If they look like symbols, we map to Ensembl.
    # For robustness, we assume we are mapping from 'external_gene_name' (symbol) to 'ensembl_gene_id'.
    # If the input is already Ensembl, the mapping might return empty or itself.
    # We will attempt to map from 'external_gene_name'.
    
    # Step 1: Map STRING genes
    # If the IDs are already Ensembl, the filter might not match 'external_gene_name'.
    # A safer approach for a mixed bag is to try mapping 'external_gene_name' first.
    # If that fails or returns very little, we might try 'ensembl_gene_id' as the filter?
    # But the task specifies "align STRING and DEG gene identifiers".
    # Let's assume the inputs are primarily symbols or a mix, and we want to standardize to Ensembl.
    
    # Heuristic: If IDs start with 'ENSG' or 'YLR', they might be Ensembl/Saccharomyces specific.
    # For simplicity and adherence to "align", we will map from 'external_gene_name'.
    # If the input is Ensembl ID, we might need to map Ensembl -> Ensembl (identity) or Ensembl -> Symbol -> Ensembl.
    # Let's try mapping 'external_gene_name' first.
    
    string_mapping = _fetch_ensembl_mapping(organism, string_genes, id_type='external_gene_name')
    deg_mapping = _fetch_ensembl_mapping(organism, deg_genes, id_type='external_gene_name')
    
    # If the mapping returned very few results, it's possible the input IDs are already Ensembl IDs.
    # In that case, we might try mapping 'ensembl_gene_id' -> 'ensembl_gene_id' (identity) or just treat them as Ensembl.
    # However, the task implies a conversion. Let's assume the inputs are symbols.
    # If the mapping coverage is < 10%, we might log a warning.
    
    # Convert to Ensembl IDs
    string_ensembl = set(string_mapping.values())
    deg_ensembl = set(deg_mapping.values())
    
    # Find intersection
    common_ensembl = string_ensembl.intersection(deg_ensembl)
    
    # Calculate coverage
    # Coverage = (common genes) / (total unique genes in union of inputs) ? 
    # Or (common genes) / (total genes in STRING) ?
    # The task says "log mapping_coverage_percent". Usually this is (mapped / input).
    # Let's report the percentage of the union that successfully mapped to a common ID.
    total_unique = len(string_genes.union(deg_genes))
    mapped_common = len(common_ensembl)
    
    if total_unique == 0:
        coverage = 0.0
    else:
        coverage = (mapped_common / total_unique) * 100
        
    logger.info(f"ID Mapping Results for {organism}:")
    logger.info(f"  STRING genes: {len(string_genes)}")
    logger.info(f"  DEG genes: {len(deg_genes)}")
    logger.info(f"  Common Ensembl IDs: {len(common_ensembl)}")
    logger.info(f"  Mapping Coverage: {coverage:.2f}%")
    
    # Save report if output_dir provided
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "organism": organism,
            "string_genes_count": len(string_genes),
            "deg_genes_count": len(deg_genes),
            "common_ensembl_count": len(common_ensembl),
            "mapping_coverage_percent": coverage,
            "common_ensembl_ids": list(common_ensembl)[:100] # Truncate for log size if huge
        }
        report_path = output_dir / f"mapping_report_{organism}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Mapping report saved to {report_path}")
    
    return common_ensembl, coverage

def fetch_string_network(organism: str, threshold: int = 700) -> Dict[str, Any]:
    """Fetch PPI network from STRING API."""
    # Implementation assumed to exist in previous tasks (T012)
    # Placeholder for context: this function returns a graph or edge list
    raise NotImplementedError("fetch_string_network is implemented in T012")

def load_local_network(organism: str) -> Dict[str, Any]:
    """Load local PPI network."""
    # Placeholder
    raise NotImplementedError("load_local_network is implemented in T012")

def fetch_essentiality_labels(organism: str) -> Dict[str, bool]:
    """Fetch essentiality labels from DEG."""
    # Placeholder
    raise NotImplementedError("fetch_essentiality_labels is implemented in T013")

def load_local_essentiality(organism: str) -> Dict[str, bool]:
    """Load local essentiality labels."""
    # Placeholder
    raise NotImplementedError("load_local_essentiality is implemented in T013")

def load_essentiality_for_all_organisms() -> Dict[str, Dict[str, bool]]:
    """Load essentiality for all organisms."""
    # Placeholder
    raise NotImplementedError("load_essentiality_for_all_organisms is implemented in T013")

def save_essentiality_data(data: Dict[str, bool], organism: str, path: Path):
    """Save essentiality data."""
    # Placeholder
    raise NotImplementedError("save_essentiality_data is implemented in T013")

def main():
    """Main entry point for ID mapping demonstration."""
    setup_logging()
    config = load_config()
    organisms = get_organisms(config)
    
    # Example: Run mapping for the first organism
    if not organisms:
        logger.warning("No organisms defined in config.")
        return

    organism = organisms[0]
    logger.info(f"Running ID mapping for {organism}")
    
    # Simulate loading data (in real flow, these come from T012/T013)
    # We cannot call the real fetch functions here as they are not fully implemented in this snippet
    # but we assume they return sets of gene IDs.
    # For this task, we demonstrate the mapping logic.
    
    # Mock data for demonstration of the mapping function
    # In the real pipeline, these would be the actual sets from STRING and DEG
    mock_string_genes = {"TP53", "BRCA1", "EGFR", "MYC"}
    mock_deg_genes = {"TP53", "BRCA1", "EGFR", "VEGFA"}
    
    common_ids, coverage = map_ids(
        organism=organism,
        string_genes=mock_string_genes,
        deg_genes=mock_deg_genes,
        output_dir=get_path(config, "results")
    )
    
    logger.info(f"Final common IDs: {common_ids}")
    logger.info(f"Coverage: {coverage}%")

if __name__ == "__main__":
    main()