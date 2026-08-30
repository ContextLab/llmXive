import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple
from config import load_config, get_config
from data_loader import fetch_marker_genes, fetch_metabolite_profiles, save_fasta_sequences
from phylo_pipeline import (
    run_concatenation_pipeline,
    run_alignment_pipeline,
    run_tree_building_pipeline,
    calculate_patristic_distance_matrix
)
from stats_engine import calculate_jaccard_dissimilarity_matrix, run_mantel_test
from report import append_validation_log, verify_sc003_retention, generate_analysis_summary
from logging_config import setup_logging, get_logger
from utils import stream_file_lines

logger = get_logger("main")

def run_pipeline(species_file: Path, output_dir: Path):
    """
    Run the full phylogenetic signal detection pipeline.
    
    Args:
        species_file: Path to the file containing species names.
        output_dir: Directory for outputs.
    """
    config = load_config()
    setup_logging(level="INFO")
    
    # 1. Load Species
    logger.info("Loading species list...")
    species_names = [line.strip() for line in stream_file_lines(species_file) if line.strip()]
    if not species_names:
        raise ValueError("No species found in input file.")
    logger.info(f"Loaded {len(species_names)} species.")

    # 2. Fetch Data
    logger.info("Fetching genomic and metabolite data...")
    try:
        gene_data = fetch_marker_genes(species_names, loci=["18S", "rbcL", "matK"])
        save_fasta_sequences(gene_data, output_dir / "raw" / "concatenated.fasta")
        metab_data = fetch_metabolite_profiles(species_names)
    except ValueError as e:
        logger.critical(f"Data fetch failed: {e}")
        raise

    # 3. Filter Valid Species
    valid_species = [s for s in species_names if s in gene_data and s in metab_data]
    total_species = len(species_names)
    retained_species = len(valid_species)
    
    logger.info(f"Valid species with both data: {retained_species}/{total_species}")
    
    # Check SC-003
    verify_sc003_retention(total_species, retained_species)

    if retained_species < 3:
        raise RuntimeError("Insufficient data for analysis (need at least 3 species).")

    # 4. Phylogeny Construction
    logger.info("Building phylogeny...")
    concat_fasta = output_dir / "raw" / "concatenated.fasta"
    if not concat_fasta.exists():
        save_fasta_sequences(gene_data, concat_fasta)
    
    run_concatenation_pipeline(concat_fasta, concat_fasta)
    aligned_fasta = run_alignment_pipeline(concat_fasta)
    tree_file = output_dir / "processed" / "tree.newick"
    run_tree_building_pipeline(aligned_fasta, tree_file)

    # 5. Distance Matrices
    logger.info("Calculating distance matrices...")
    phylo_dist = calculate_patristic_distance_matrix(tree_file, valid_species)
    phylo_dist.to_csv(output_dir / "processed" / "phylo_dist_matrix.csv")
    
    metab_dist = calculate_jaccard_dissimilarity_matrix(metab_data, valid_species)
    metab_dist.to_csv(output_dir / "processed" / "metab_dist_matrix.csv")

    # 6. Mantel Test
    logger.info("Running Mantel test...")
    mantel_result = run_mantel_test(phylo_dist, metab_dist, permutations=999)
    
    # Log SC-001
    p_val = mantel_result["p_value"]
    threshold = 0.1 if retained_species <= 10 else 0.05
    status = "PASS" if p_val < threshold else "FAIL"
    append_validation_log(f"SC-001: p={p_val:.4f} (Threshold={threshold}) -> {status}")

    # 7. Summary
    generate_analysis_summary({
        "mantel_r": mantel_result["r"],
        "mantel_p": p_val
    })

    logger.info("Pipeline completed successfully.")

def main():
    config = load_config()
    species_file = Path(config.data_dir) / "raw" / "test_species_10.txt"
    output_dir = Path(config.output_dir)
    
    if not species_file.exists():
        logger.error(f"Species file not found: {species_file}")
        sys.exit(1)
    
    run_pipeline(species_file, output_dir)

if __name__ == "__main__":
    main()
