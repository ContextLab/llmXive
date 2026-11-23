import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from config import load_config, get_config
from data_loader import fetch_marker_genes, fetch_metabolite_profiles, save_fasta_sequences
from phylo_pipeline import (
    run_concatenation_pipeline,
    run_alignment_pipeline,
    run_tree_building_pipeline,
    calculate_patristic_distance_matrix
)
from stats_engine import calculate_jaccard_dissimilarity_matrix, run_mantel_test, save_mantel_results
from report import append_validation_log, verify_sc003_retention, generate_analysis_summary
from logging_config import setup_logging, get_logger
from utils import stream_file_lines

logger = get_logger("main")

def run_pipeline(species_file: Path, output_dir: Path, step: Optional[str] = None):
    """
    Run the phylogenetic signal detection pipeline with strict data loss validation.

    Constraints:
    - Distinguish between 'total data loss' (>20% species missing BOTH sequence AND metabolite) -> HALT.
    - 'Partial exclusion' (missing KEGG only) -> EXCLUDE from matrix, RETAIN in tree, LOG warning.
    - Data Loss Formula: (Species with NO Sequence AND NO Metabolite) / Total Target.
    - Total Target Source: Read from `data/raw/species_list.txt` (or provided species_file).
    """
    config = load_config()
    setup_logging(level="INFO")
    
    # 1. Load Species
    logger.info("Loading species list...")
    species_names = [line.strip() for line in stream_file_lines(species_file) if line.strip()]
    if not species_names:
        raise ValueError("No species found in input file.")
    
    total_target = len(species_names)
    logger.info(f"Total target species: {total_target}")

    # 2. Fetch Data
    logger.info("Fetching genomic and metabolite data...")
    gene_data: Dict[str, str] = {}
    metab_data: Dict[str, List[str]] = {}
    
    # Fetch sequences
    if step is None or step == "download":
        try:
            gene_data = fetch_marker_genes(species_names, loci=["18S", "rbcL", "matK"])
            # Save raw sequences immediately (T021 requirement)
            raw_dir = output_dir / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            save_fasta_sequences(gene_data, raw_dir / "concatenated.fasta")
            logger.info(f"Saved raw sequences to {raw_dir / 'concatenated.fasta'}")
        except ValueError as e:
            logger.critical(f"Data fetch failed: {e}")
            raise

    # Fetch metabolites
    if step is None or step == "download":
        try:
            metab_data = fetch_metabolite_profiles(species_names)
        except ValueError as e:
            logger.critical(f"Metabolite fetch failed: {e}")
            raise

    # 3. Data Loss Analysis & Filtering
    # Identify species with NO sequence AND NO metabolite
    missing_both: Set[str] = set()
    missing_metab_only: Set[str] = set()
    missing_seq_only: Set[str] = set()
    
    for species in species_names:
        has_seq = species in gene_data and len(gene_data[species]) > 0
        has_metab = species in metab_data and len(metab_data[species]) > 0
        
        if not has_seq and not has_metab:
            missing_both.add(species)
        elif not has_metab:
            missing_metab_only.add(species)
        elif not has_seq:
            missing_seq_only.add(species)
    
    total_missing_both = len(missing_both)
    data_loss_ratio = total_missing_both / total_target
    
    logger.info(f"Species with NO Sequence AND NO Metabolite: {total_missing_both}")
    logger.info(f"Species with missing Metabolite only (partial exclusion): {len(missing_metab_only)}")
    logger.info(f"Species with missing Sequence only: {len(missing_seq_only)}")
    
    # SC-003 Check: Total Data Loss Threshold (>20%)
    threshold = 0.20
    if data_loss_ratio > threshold:
        error_msg = (
            f"CRITICAL DATA LOSS: {data_loss_ratio:.2%} of species missing BOTH data types "
            f"({total_missing_both}/{total_target}). Threshold exceeded ({threshold:.0%}). HALTING."
        )
        logger.error(error_msg)
        append_validation_log(f"SC-003: Retention {1-data_loss_ratio:.2%} (FAIL - Exceeds 20% loss)")
        raise RuntimeError(error_msg)
    
    # Partial Exclusion Handling
    # Species missing KEGG only -> EXCLUDE from matrix, RETAIN in tree (if sequence exists)
    # Species missing Sequence only -> EXCLUDE from tree (cannot build phylogeny)
    
    # Valid for Phylogeny: Must have sequence
    valid_for_phylo = [s for s in species_names if s in gene_data and len(gene_data[s]) > 0]
    
    # Valid for Metabolite Matrix: Must have metabolite data
    valid_for_metab = [s for s in species_names if s in metab_data and len(metab_data[s]) > 0]
    
    # Intersection for Mantel Test (needs both)
    valid_for_mantel = [s for s in valid_for_phylo if s in valid_for_metab]
    
    logger.info(f"Species valid for Phylogeny: {len(valid_for_phylo)}")
    logger.info(f"Species valid for Metabolite Matrix: {len(valid_for_metab)}")
    logger.info(f"Species valid for Mantel Test (Intersection): {len(valid_for_mantel)}")

    # Log partial exclusions
    for s in missing_metab_only:
        logger.warning(f"Partial Exclusion (Metabolite missing): {s} - Retained in tree, excluded from matrix.")
    for s in missing_seq_only:
        logger.warning(f"Partial Exclusion (Sequence missing): {s} - Excluded from tree.")

    # SC-003 Retention Calculation (Species with BOTH / Total Target)
    verify_sc003_retention(total_target, len(valid_for_mantel))

    if len(valid_for_mantel) < 3:
        raise RuntimeError(f"Insufficient data for Mantel test (need at least 3 species with both data types). Found: {len(valid_for_mantel)}")

    # 4. Phylogeny Construction (Only if step is None or 'phylogeny')
    if step is None or step == "phylogeny":
        logger.info("Building phylogeny...")
        raw_dir = output_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        concat_fasta = raw_dir / "concatenated.fasta"
        
        if not concat_fasta.exists():
            save_fasta_sequences(gene_data, concat_fasta)
        
        # Run concatenation (idempotent)
        run_concatenation_pipeline(concat_fasta, concat_fasta)
        
        # Run alignment
        aligned_fasta = run_alignment_pipeline(concat_fasta)
        
        # Build tree
        tree_file = output_dir / "processed" / "tree.newick"
        processed_dir = output_dir / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        run_tree_building_pipeline(aligned_fasta, tree_file)
        logger.info(f"Tree saved to {tree_file}")

    # 5. Distance Matrices
    phylo_dist_matrix_path = output_dir / "processed" / "phylo_dist_matrix.csv"
    metab_dist_matrix_path = output_dir / "processed" / "metab_dist_matrix.csv"
    
    # Check if we need to recalculate or load
    if step is None or step == "stats":
        logger.info("Calculating distance matrices...")
        
        # Calculate Phylogenetic Distance
        tree_file = output_dir / "processed" / "tree.newick"
        if not tree_file.exists():
            raise FileNotFoundError(f"Tree file not found: {tree_file}. Run phylogeny step first.")
        
        phylo_dist = calculate_patristic_distance_matrix(tree_file, valid_for_mantel)
        phylo_dist.to_csv(phylo_dist_matrix_path)
        
        # Calculate Metabolite Dissimilarity
        metab_dist = calculate_jaccard_dissimilarity_matrix(metab_data, valid_for_mantel)
        metab_dist.to_csv(metab_dist_matrix_path)

    # 6. Mantel Test
    if step is None or step == "stats":
        logger.info("Running Mantel test...")
        phylo_dist = calculate_patristic_distance_matrix(output_dir / "processed" / "tree.newick", valid_for_mantel)
        metab_dist = calculate_jaccard_dissimilarity_matrix(metab_data, valid_for_mantel)
        
        mantel_result = run_mantel_test(phylo_dist, metab_dist, permutations=999)
        
        # Save Results (T019 requirement)
        save_mantel_results(mantel_result, output_dir / "processed" / "mantel_results.json")
        
        # Log SC-001
        p_val = mantel_result["p_value"]
        threshold_p = 0.1 if len(valid_for_mantel) <= 10 else 0.05
        status = "PASS" if p_val < threshold_p else "FAIL"
        append_validation_log(f"SC-001: p={p_val:.4f} (Threshold={threshold_p}) -> {status}")

    # 7. Summary
    if step is None:
        logger.info("Generating analysis summary...")
        # Load results if not in memory (for safety)
        mantel_results_path = output_dir / "processed" / "mantel_results.json"
        if mantel_results_path.exists():
            import json
            with open(mantel_results_path) as f:
                res = json.load(f)
            generate_analysis_summary({
                "mantel_r": res["r"],
                "mantel_p": res["p_value"]
            })
        logger.info("Pipeline completed successfully.")

def main():
    import argparse
    config = load_config()
    
    parser = argparse.ArgumentParser(description="Phylogenetic Signal Pipeline")
    parser.add_argument("--step", type=str, default=None,
                        choices=["download", "phylogeny", "stats", "viz"],
                        help="Specific step to run. If None, runs full pipeline.")
    parser.add_argument("--species-list", type=str, default=None,
                        help="Path to species list file. Defaults to config.")
    
    args = parser.parse_args()
    
    # Determine species file
    if args.species_list:
        species_file = Path(args.species_list)
    else:
        # Default from config or quickstart
        species_file = Path(config.data_dir) / "raw" / "test_species_10.txt"
        if not species_file.exists():
            # Fallback to common location if config path fails
            species_file = Path("data/raw/test_species_10.txt")
    
    output_dir = Path(config.output_dir)
    
    if not species_file.exists():
        logger.error(f"Species file not found: {species_file}")
        sys.exit(1)
    
    # Ensure output directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "raw").mkdir(parents=True, exist_ok=True)
    (output_dir / "processed").mkdir(parents=True, exist_ok=True)
    
    run_pipeline(species_file, output_dir, step=args.step)

if __name__ == "__main__":
    main()