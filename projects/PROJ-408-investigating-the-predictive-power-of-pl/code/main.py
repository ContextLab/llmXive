"""
Main orchestration logic for the pipeline.
Implements T020a (Orchestration & Data Loss Logic) and T020b (SC-003 Verification).
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple

from config import load_config, get_config
from logging_config import setup_logging, get_logger, log_pipeline_step
from data_loader import fetch_marker_genes, fetch_metabolite_profiles, FetchResult
from phylo_pipeline import (
    run_concatenation_pipeline, 
    run_alignment_pipeline, 
    run_tree_building_pipeline,
    calculate_patristic_distance_matrix
)
from stats_engine import calculate_jaccard_dissimilarity_matrix, run_mantel_test, save_mantel_results
from utils import verify_checksum

logger = get_logger(__name__)

def run_pipeline(species_file: Path, config) -> Tuple[float, float]:
    """
    Run the full phylogeny-metabolite pipeline.
    
    Logic for T020a:
    1. Distinguish 'total data loss' (>20% missing BOTH) -> HALT
    2. Distinguish 'partial exclusion' (missing KEGG only) -> EXCLUDE from matrix, RETAIN in tree
    """
    log_pipeline_step("START", "Full Pipeline Execution")

    # 1. Load Species List
    if not species_file.exists():
        raise FileNotFoundError(f"Species list not found: {species_file}")
    
    with open(species_file, 'r') as f:
        target_species = [line.strip() for line in f if line.strip()]
    
    total_species = len(target_species)
    logger.info(f"Target species count: {total_species}")

    # 2. Fetch Data & Track Loss
    gene_data: Dict[str, Dict[str, str]] = {}
    metabolite_data: Dict[str, Dict[str, bool]] = {}
    missing_both_count = 0
    missing_kegg_only_count = 0
    missing_gene_only_count = 0

    for species in target_species:
        # Fetch Genes (Sequence data)
        gene_res: FetchResult = fetch_marker_genes(species, ["18S", "rbcL", "matK"])
        has_gene = gene_res.success and bool(gene_res.sequences)
        
        if has_gene:
            gene_data[species] = gene_res.sequences
        else:
            logger.warning(f"Missing gene data for {species}: {gene_res.error or 'Unknown error'}")

        # Fetch Metabolites (KEGG profiles)
        meta_res = fetch_metabolite_profiles(species)
        has_meta = meta_res is not None and len(meta_res) > 0
        
        if has_meta:
            metabolite_data[species] = meta_res
        else:
            logger.warning(f"Missing metabolite data for {species} (KEGG entry not found or empty)")

        # Classify Loss for T020a Logic
        if not has_gene and not has_meta:
            missing_both_count += 1
            logger.error(f"TOTAL LOSS: {species} missing BOTH sequence and metabolite data.")
        elif not has_meta:
            # Missing KEGG only -> EXCLUDE from matrix, RETAIN in tree
            missing_kegg_only_count += 1
            logger.info(f"PARTIAL EXCLUSION: {species} missing KEGG. Will be in tree, excluded from metabolite matrix.")
        elif not has_gene:
            missing_gene_only_count += 1
            logger.info(f"PARTIAL EXCLUSION: {species} missing gene data. Will be excluded from tree.")

    # 3. Data Integrity Check (T020a - SC-003)
    # Total data loss > 20% -> HALT
    loss_threshold = 0.20
    if missing_both_count > (total_species * loss_threshold):
        error_msg = f"Total data loss exceeds {loss_threshold*100}% ({missing_both_count}/{total_species} species missing BOTH). HALTING."
        logger.error(error_msg)
        
        # SC-003 Verification: FAIL
        log_entry = f"SC-003: Retention 0% (FAIL - Data loss > 20%)\n"
        with open(config.output_reports_dir / "validation_log.txt", 'a') as f:
            f.write(log_entry)
        
        raise RuntimeError(error_msg)
    
    # Calculate Retention (Species with at least gene data, as tree is the backbone)
    # If we have < 3 species for tree, we can't proceed anyway.
    retention_count = len(gene_data)
    if retention_count == 0:
        raise RuntimeError("No species with gene data found. Cannot build tree.")
        
    retention_pct = (retention_count / total_species) * 100
    logger.info(f"SC-003: Retention {retention_pct:.1f}% (PASS)")
    
    # Write SC-003 Pass status
    log_entry = f"SC-003: Retention {retention_pct:.1f}% (PASS)\n"
    with open(config.output_reports_dir / "validation_log.txt", 'a') as f:
        f.write(log_entry)

    # 4. Phylogeny Construction
    # We need at least 3 species to build a meaningful tree
    if retention_count < 3:
        raise ValueError(f"Insufficient species with gene data ({retention_count}) to build a phylogenetic tree. Minimum 3 required.")

    concat_fasta = config.data_processed_dir / "concatenated.fasta"
    aligned_fasta = config.data_processed_dir / "aligned.fasta"
    tree_file = config.data_processed_dir / "tree.newick"

    logger.info(f"Building tree for {retention_count} species...")
    run_concatenation_pipeline(gene_data, concat_fasta)
    run_alignment_pipeline(concat_fasta, aligned_fasta)
    run_tree_building_pipeline(aligned_fasta, tree_file)

    # 5. Distance Matrices
    phylo_matrix = calculate_patristic_distance_matrix(tree_file)
    
    # Filter metabolite data to species present in the tree (common species)
    # This implements the "Partial Exclusion" logic:
    # - Species with gene data are in the tree.
    # - Species without metabolite data are in the tree but NOT in the metabolite matrix.
    # - Mantel test requires intersection.
    tree_species = set(phylo_matrix.species)
    meta_species = set(metabolite_data.keys())
    common_species = list(tree_species & meta_species)
    
    logger.info(f"Common species for Mantel test: {len(common_species)} (Tree: {len(tree_species)}, Metabolite: {len(meta_species)})")
    
    if len(common_species) < 3:
        raise ValueError(f"Not enough common species ({len(common_species)}) for Mantel test. Minimum 3 required.")
    
    # Prepare matrices for Mantel test
    # Filter metabolite data to common species
    meta_subset = {s: metabolite_data[s] for s in common_species}
    meta_matrix = calculate_jaccard_dissimilarity_matrix(meta_subset)
    
    # Re-index phylo matrix to match the order of common_species
    phylo_subset = phylo_matrix.get_subset_matrix(common_species)

    # 6. Mantel Test
    logger.info("Running Mantel test...")
    r, p, null_dist = run_mantel_test(
        phylo_subset.values, 
        meta_matrix.values, 
        permutations=999
    )
    logger.info(f"Mantel Test Result: r={r:.4f}, p={p:.4f}")

    # 7. Save Results
    save_mantel_results(r, p, null_dist, config.data_processed_dir / "mantel_results.json")

    # 8. Validation Log (SC-001)
    status = "PASS" if p < 0.05 else "FAIL"
    log_entry = f"SC-001: p = {p:.4f} ({status})\n"
    with open(config.output_reports_dir / "validation_log.txt", 'a') as f:
        f.write(log_entry)
    
    logger.info(f"Validation SC-001: {status}")

    log_pipeline_step("COMPLETE", "Pipeline finished successfully")
    return r, p

def main():
    """Entry point for the pipeline."""
    config = load_config()
    setup_logging(level=logging.INFO)
    
    # Default input species file
    species_file = config.data_raw_dir / "test_species_10.txt"
    if not species_file.exists():
        # Fallback relative to script location
        fallback = Path(__file__).parent.parent / "data/raw/test_species_10.txt"
        if fallback.exists():
            species_file = fallback
        else:
            raise FileNotFoundError(f"Could not find species list at {config.data_raw_dir} or {fallback}")
    
    logger.info(f"Starting pipeline with species file: {species_file}")
    
    try:
        r, p = run_pipeline(species_file, config)
        logger.info(f"Pipeline completed successfully. Final r={r}, p={p}")
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()