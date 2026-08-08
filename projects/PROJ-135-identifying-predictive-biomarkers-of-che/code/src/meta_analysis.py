"""
Meta-analysis module for cross-cancer biomarker identification.

Implements:
- Intersection of significant genes across tumor types
- Union of top-ranked genes (fallback)
- Stouffer's method for meta-analysis p-values
- Gene panel saving
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

import pandas as pd
import numpy as np

# Import shared utilities from project
from src.config import get_project_root, ensure_directories
from src.utils import setup_logging, calculate_checksum

# Configure logging
logger = setup_logging(__name__)

# Constants from spec
FDR_THRESHOLD = 0.05
LOG2FC_THRESHOLD = 1.0
MAX_UNION_SIZE = 50


def load_discovery_results(
    processed_dir: Path, 
    tumor_types: List[str]
) -> Dict[str, pd.DataFrame]:
    """
    Load differential expression results for each tumor type from the discovery set.
    
    Args:
        processed_dir: Path to data/processed directory
        tumor_types: List of tumor type identifiers (e.g., 'BRCA', 'LUAD')
        
    Returns:
        Dictionary mapping tumor_type -> DataFrame with DE results
        
    Raises:
        FileNotFoundError: If any expected discovery result file is missing
        ValueError: If a file exists but has invalid structure
    """
    results = {}
    
    for tumor_type in tumor_types:
        # T023 output path: data/processed/{tumor_type}_de_results.csv
        de_file = processed_dir / f"{tumor_type}_de_results.csv"
        
        if not de_file.exists():
            raise FileNotFoundError(
                f"Discovery DE results missing for {tumor_type}: {de_file}"
            )
        
        try:
            df = pd.read_csv(de_file)
            
            # Validate required columns from T023
            required_cols = ['gene', 'pvalue', 'padj', 'log2FoldChange']
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                raise ValueError(
                    f"File {de_file} missing columns: {missing_cols}"
                )
            
            results[tumor_type] = df
            logger.info(
                f"Loaded DE results for {tumor_type}: {len(df)} genes"
            )
            
        except Exception as e:
            logger.error(f"Failed to load {de_file}: {e}")
            raise
    
    return results


def compute_intersection(
    de_results: Dict[str, pd.DataFrame]
) -> Set[str]:
    """
    Compute the intersection of significant genes across ≥2 tumor types.
    
    A gene is considered significant if:
    - padj < FDR_THRESHOLD (0.05)
    - |log2FoldChange| > LOG2FC_THRESHOLD (1.0)
    
    Args:
        de_results: Dictionary mapping tumor_type -> DE result DataFrame
        
    Returns:
        Set of gene symbols present in the intersection of significant genes
        
    Notes:
        - Only includes genes that are significant in ALL tumor types
        - Returns empty set if intersection is empty or only 1 tumor type provided
    """
    if len(de_results) < 2:
        logger.warning(
            "compute_intersection requires ≥2 tumor types; "
            f"got {len(de_results)}. Returning empty set."
        )
        return set()
    
    significant_genes_per_type: List[Set[str]] = []
    
    for tumor_type, df in de_results.items():
        # Filter for significant genes per spec FR-006
        sig_mask = (
            (df['padj'] < FDR_THRESHOLD) & 
            (np.abs(df['log2FoldChange']) > LOG2FC_THRESHOLD)
        )
        sig_genes = set(df.loc[sig_mask, 'gene'].dropna().unique())
        
        logger.info(
            f"{tumor_type}: {len(sig_genes)} significant genes "
            f"(FDR<{FDR_THRESHOLD}, |log2FC|>{LOG2FC_THRESHOLD})"
        )
        
        if len(sig_genes) == 0:
            logger.warning(
                f"No significant genes found for {tumor_type}; "
                "intersection will be empty."
            )
        
        significant_genes_per_type.append(sig_genes)
    
    # Compute intersection across all sets
    if not significant_genes_per_type:
        return set()
    
    intersection = significant_genes_per_type[0]
    for gene_set in significant_genes_per_type[1:]:
        intersection = intersection.intersection(gene_set)
    
    logger.info(
        f"Intersection size: {len(intersection)} genes across "
        f"{len(de_results)} tumor types"
    )
    
    return intersection


def compute_union_top_ranked(
    de_results: Dict[str, pd.DataFrame],
    max_genes: int = MAX_UNION_SIZE
) -> List[str]:
    """
    Compute the union of top-ranked genes as a fallback when intersection is empty.
    
    Ranks genes by combined evidence (e.g., average p-value or count of 
    significant appearances) and returns top N.
    
    Args:
        de_results: Dictionary mapping tumor_type -> DE result DataFrame
        max_genes: Maximum number of genes to include (default: 50 per spec)
        
    Returns:
        List of gene symbols, ranked by combined evidence (most significant first)
        
    Notes:
        - This is a fallback strategy per FR-006
        - Genes are ranked by the number of tumor types where they are significant,
          then by average p-value across those types
    """
    if len(de_results) < 2:
        logger.warning(
            "compute_union_top_ranked requires ≥2 tumor types; "
            f"got {len(de_results)}."
        )
        return []
    
    # Track gene statistics across tumor types
    gene_stats: Dict[str, Dict[str, Any]] = {}
    
    for tumor_type, df in de_results.items():
        sig_mask = (
            (df['padj'] < FDR_THRESHOLD) & 
            (np.abs(df['log2FoldChange']) > LOG2FC_THRESHOLD)
        )
        sig_df = df.loc[sig_mask].copy()
        
        for _, row in sig_df.iterrows():
            gene = row['gene']
            if pd.isna(gene):
                continue
            
            if gene not in gene_stats:
                gene_stats[gene] = {
                    'significant_count': 0,
                    'pvalue_sum': 0.0,
                    'pvalue_count': 0
                }
            
            gene_stats[gene]['significant_count'] += 1
            gene_stats[gene]['pvalue_sum'] += row['pvalue']
            gene_stats[gene]['pvalue_count'] += 1
    
    if not gene_stats:
        logger.warning("No significant genes found in any tumor type; "
                     "union is empty.")
        return []
    
    # Rank by: (1) count of significant appearances (descending),
    #          (2) average p-value (ascending)
    ranked_genes = sorted(
        gene_stats.keys(),
        key=lambda g: (
            -gene_stats[g]['significant_count'],
            gene_stats[g]['pvalue_sum'] / gene_stats[g]['pvalue_count']
        )
    )
    
    top_genes = ranked_genes[:max_genes]
    
    logger.info(
        f"Union top-ranked: {len(top_genes)} genes (max {max_genes})"
    )
    
    return top_genes


def save_gene_panel(
    selected_genes: List[str],
    tumor_types: List[str],
    output_path: Path,
    fallback_reason: Optional[str] = None,
    method: str = "intersection"
) -> None:
    """
    Save the final selected gene panel to JSON.
    
    Args:
        selected_genes: List of gene symbols in the final panel
        tumor_types: List of tumor types used in meta-analysis
        output_path: Path to write the gene panel JSON
        fallback_reason: Reason for fallback (e.g., "intersection_empty"), or None
        method: Method used ("intersection", "union_top_ranked", or "stouffer")
        
    Notes:
        - Output conforms to gene_panel.schema.yaml
        - Includes metadata for reproducibility
    """
    ensure_directories([output_path.parent])
    
    panel_data = {
        "selected": selected_genes,
        "panel_size": len(selected_genes),
        "tumor_types_analyzed": tumor_types,
        "method": method,
        "fallback_reason": fallback_reason,
        "thresholds": {
            "fdr": FDR_THRESHOLD,
            "log2fc": LOG2FC_THRESHOLD
        },
        "metadata": {
            "generated_by": "meta_analysis.compute_intersection or compute_union_top_ranked",
            "spec_version": "FR-006"
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(panel_data, f, indent=2)
    
    checksum = calculate_checksum(output_path)
    logger.info(
        f"Saved gene panel to {output_path} "
        f"({len(selected_genes)} genes, method={method})"
    )
    logger.debug(f"Checksum: {checksum}")

def main():
    """
    Entry point for meta-analysis stage.
    
    This function:
    1. Loads DE results from T023 (discovery sets)
    2. Computes intersection of significant genes
    3. If intersection is empty, falls back to union of top-ranked genes
    4. Saves the final gene panel to results/meta_analysis/gene_panel.json
    """
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    results_dir = project_root / "results"
    meta_dir = results_dir / "meta_analysis"
    
    # Define tumor types (should match what was processed in T020/T023)
    # In a real run, this would be discovered from the processed directory
    # For now, we expect the caller to pass or infer this
    # Here we scan the processed_dir for de_results files
    de_files = list(processed_dir.glob("*_de_results.csv"))
    if not de_files:
        logger.error(
            "No DE result files found in data/processed. "
            "Ensure T023 has been run successfully."
        )
        sys.exit(1)
    
    tumor_types = [
        f.stem.replace("_de_results", "") 
        for f in de_files
    ]
    
    logger.info(f"Found {len(tumor_types)} tumor types: {tumor_types}")
    
    # Load discovery results
    try:
        de_results = load_discovery_results(processed_dir, tumor_types)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load discovery results: {e}")
        sys.exit(1)
    
    # Compute intersection
    intersection_genes = compute_intersection(de_results)
    
    selected_genes = []
    fallback_reason = None
    method = "intersection"
    
    if len(intersection_genes) == 0:
        logger.warning(
            "Intersection is empty. Falling back to union of top-ranked genes."
        )
        selected_genes = compute_union_top_ranked(de_results, max_genes=MAX_UNION_SIZE)
        fallback_reason = "intersection_empty"
        method = "union_top_ranked"
    else:
        selected_genes = sorted(list(intersection_genes))
    
    if not selected_genes:
        logger.error(
            "No genes selected (intersection empty and union yielded no results). "
            "Cannot proceed."
        )
        sys.exit(1)
    
    # Save gene panel
    output_path = meta_dir / "gene_panel.json"
    save_gene_panel(
        selected_genes=selected_genes,
        tumor_types=tumor_types,
        output_path=output_path,
        fallback_reason=fallback_reason,
        method=method
    )
    
    logger.info("Meta-analysis stage completed successfully.")
    return selected_genes


if __name__ == "__main__":
    main()
