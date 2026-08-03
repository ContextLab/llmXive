"""
Meta-analysis module for biomarker discovery.
Implements intersection of significant genes across tumor types (FR-006).
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

from src.config import get_project_root
from src.utils import ensure_path_exists

# Configure logging
logger = logging.getLogger(__name__)

def load_discovery_results(tumor_type: str, project_root: Path) -> Dict[str, Any]:
    """
    Load the differential expression results for a specific tumor type.
    Expects files named: {tumor_type}_discovery_de_results.json
    
    Args:
        tumor_type: The tumor type identifier (e.g., 'BRCA', 'LUAD')
        project_root: The root path of the project
        
    Returns:
        Dictionary containing DE results with 'significant_genes' key
        
    Raises:
        FileNotFoundError: If the results file does not exist
        ValueError: If the file format is invalid
    """
    results_file = project_root / "data" / "processed" / f"{tumor_type}_discovery_de_results.json"
    
    if not results_file.exists():
        raise FileNotFoundError(f"Discovery DE results not found for {tumor_type}: {results_file}")
    
    try:
        with open(results_file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {results_file}: {e}")
    
    if 'significant_genes' not in data:
        raise ValueError(f"Missing 'significant_genes' key in {results_file}")
    
    return data

def compute_intersection(tumor_types: List[str], project_root: Optional[Path] = None) -> List[str]:
    """
    Compute the intersection of significant genes across ≥2 tumor types (FR-006).
    
    This function:
    1. Loads discovery DE results for each tumor type
    2. Extracts the set of significant genes from each
    3. Computes the intersection across all provided tumor types
    4. Returns the list of genes present in ALL tumor types
    
    Args:
        tumor_types: List of tumor type identifiers to intersect
        project_root: Optional project root path (defaults to config)
        
    Returns:
        List of gene symbols that are significant in ALL tumor types
        
    Raises:
        ValueError: If fewer than 2 tumor types are provided
        FileNotFoundError: If any tumor type's results file is missing
        RuntimeError: If the intersection is empty (handled by caller)
    """
    if project_root is None:
        project_root = get_project_root()
    
    if len(tumor_types) < 2:
        raise ValueError(f"Intersection requires at least 2 tumor types, got {len(tumor_types)}")
    
    logger.info(f"Computing intersection of significant genes across {len(tumor_types)} tumor types: {tumor_types}")
    
    gene_sets: List[Set[str]] = []
    
    for tumor_type in tumor_types:
        try:
            results = load_discovery_results(tumor_type, project_root)
            genes = set(results['significant_genes'])
            gene_sets.append(genes)
            logger.info(f"  {tumor_type}: {len(genes)} significant genes")
        except FileNotFoundError as e:
            logger.error(f"Cannot load results for {tumor_type}: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid results format for {tumor_type}: {e}")
            raise
    
    # Compute intersection
    intersection = gene_sets[0]
    for gene_set in gene_sets[1:]:
        intersection = intersection.intersection(gene_set)
    
    logger.info(f"Intersection size: {len(intersection)} genes")
    
    if len(intersection) == 0:
        logger.warning("Intersection is empty - no genes common to all tumor types")
        return []
    
    return sorted(list(intersection))

def compute_union_top_ranked(tumor_types: List[str], project_root: Optional[Path] = None, 
                             max_genes: int = 50) -> List[str]:
    """
    Compute the union of top-ranked genes across tumor types (fallback for empty intersection).
    
    This is used when the intersection is empty. It takes the top N genes from each
    tumor type (ranked by p-value or log2FC) and returns their union.
    
    Args:
        tumor_types: List of tumor type identifiers
        project_root: Optional project root path
        max_genes: Maximum number of top genes to consider from each tumor type
        
    Returns:
        List of gene symbols from the union of top-ranked genes
    """
    if project_root is None:
        project_root = get_project_root()
    
    logger.info(f"Computing union of top {max_genes} genes across {len(tumor_types)} tumor types")
    
    union_genes: Set[str] = set()
    
    for tumor_type in tumor_types:
        try:
            results = load_discovery_results(tumor_type, project_root)
            
            # Get all significant genes with their rankings
            # Assumes results has 'significant_genes' as list of dicts with 'gene', 'pvalue', 'log2fc'
            genes_data = results.get('significant_genes', [])
            
            if isinstance(genes_data, list) and len(genes_data) > 0 and isinstance(genes_data[0], dict):
                # Sort by p-value (ascending) or log2FC (descending)
                sorted_genes = sorted(
                    genes_data, 
                    key=lambda x: (x.get('pvalue', float('inf')), -x.get('log2fc', 0))
                )
                
                # Take top max_genes
                top_genes = [g['gene'] for g in sorted_genes[:max_genes]]
                union_genes.update(top_genes)
                logger.info(f"  {tumor_type}: added {len(top_genes)} top genes")
            elif isinstance(genes_data, list):
                # If it's a list of strings, just take top max_genes
                top_genes = genes_data[:max_genes]
                union_genes.update(top_genes)
                logger.info(f"  {tumor_type}: added {len(top_genes)} genes")
            
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Skipping {tumor_type} in union computation: {e}")
            continue
    
    logger.info(f"Union size: {len(union_genes)} genes")
    return sorted(list(union_genes))

def save_gene_panel(gene_panel: List[str], output_path: Path, 
                   intersection_used: bool = True, 
                   fallback_reason: Optional[str] = None) -> None:
    """
    Save the final gene panel to a JSON file.
    
    Args:
        gene_panel: List of gene symbols in the final panel
        output_path: Path to save the JSON file
        intersection_used: Whether intersection was used (True) or fallback (False)
        fallback_reason: Reason for fallback if applicable (e.g., "intersection_empty")
    """
    ensure_path_exists(output_path.parent)
    
    panel_data = {
        "genes": gene_panel,
        "panel_size": len(gene_panel),
        "method": "intersection" if intersection_used else "union_fallback",
        "fallback_reason": fallback_reason if not intersection_used else None
    }
    
    with open(output_path, 'w') as f:
        json.dump(panel_data, f, indent=2)
    
    logger.info(f"Saved gene panel with {len(gene_panel)} genes to {output_path}")

def main():
    """
    Main entry point for meta-analysis intersection computation.
    This function can be called from the main orchestrator or run standalone.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    project_root = get_project_root()
    
    # Example: Load tumor types from a configuration or derive from available files
    # In a real scenario, this would come from the discovery stage output
    available_tumor_types = [
        "BRCA",  # Breast Invasive Carcinoma
        "LUAD",  # Lung Adenocarcinoma
        "COAD"   # Colon Adenocarcinoma
    ]
    
    # Filter to only those that have results files
    valid_tumor_types = []
    for tt in available_tumor_types:
        results_file = project_root / "data" / "processed" / f"{tt}_discovery_de_results.json"
        if results_file.exists():
            valid_tumor_types.append(tt)
    
    if len(valid_tumor_types) < 2:
        logger.error(f"Need at least 2 tumor types with results, found {len(valid_tumor_types)}")
        sys.exit(1)
    
    logger.info(f"Found {len(valid_tumor_types)} tumor types with DE results: {valid_tumor_types}")
    
    # Compute intersection
    try:
        intersection_genes = compute_intersection(valid_tumor_types, project_root)
        
        if len(intersection_genes) > 0:
            logger.info(f"Intersection successful: {len(intersection_genes)} genes")
            output_path = project_root / "results" / "meta_analysis" / "gene_panel.json"
            save_gene_panel(intersection_genes, output_path, intersection_used=True)
        else:
            logger.info("Intersection empty, falling back to union of top-ranked genes")
            union_genes = compute_union_top_ranked(valid_tumor_types, project_root, max_genes=50)
            output_path = project_root / "results" / "meta_analysis" / "gene_panel.json"
            save_gene_panel(union_genes, output_path, intersection_used=False, 
                           fallback_reason="intersection_empty")
            
    except Exception as e:
        logger.error(f"Meta-analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
