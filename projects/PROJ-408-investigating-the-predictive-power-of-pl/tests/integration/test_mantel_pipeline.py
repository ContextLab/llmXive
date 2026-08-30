"""
Integration test for full pipeline run on a diverse set of species (T011).

Input: data/raw/test_species_10.txt
Output: data/processed/test_tree.newick
Assertion: assert p-value < 0.05 (or < 0.1 for small sample)

This test verifies the end-to-end execution of the phylogenetic signal detection
pipeline on a small, diverse set of species.
"""
import os
import sys
import json
import logging
from pathlib import Path
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import load_config, get_config
from data_loader import fetch_marker_genes, fetch_metabolite_profiles, save_fasta_sequences
from phylo_pipeline import (
    run_concatenation_pipeline,
    run_alignment_pipeline,
    run_tree_building_pipeline,
    calculate_patristic_distance_matrix
)
from stats_engine import calculate_jaccard_dissimilarity_matrix, run_mantel_test
from report import append_validation_log
from logging_config import setup_logging, get_logger
from utils import stream_file_lines

# Configure logging for the test
setup_logging(level="INFO")
logger = get_logger("test_mantel_pipeline")

def test_full_pipeline_run():
    """
    Run the full pipeline on the test species list and verify outputs.
    """
    config = load_config()
    
    # Paths
    input_species_file = PROJECT_ROOT / "data/raw/test_species_10.txt"
    output_tree_file = PROJECT_ROOT / "data/processed/test_tree.newick"
    output_mantel_file = PROJECT_ROOT / "data/processed/test_mantel_results.json"
    output_phylo_dist = PROJECT_ROOT / "data/processed/test_phylo_dist_matrix.csv"
    output_metab_dist = PROJECT_ROOT / "data/processed/test_metab_dist_matrix.csv"
    
    # Ensure output directories exist
    output_tree_file.parent.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "output/reports").mkdir(parents=True, exist_ok=True)

    # 1. Load species list
    if not input_species_file.exists():
        # Create a minimal test list if missing (should be provided by T013/T014 context)
        # Using a small set of diverse plants known to have KEGG data
        species_list = [
            "Arabidopsis thaliana",
            "Solanum lycopersicum",
            "Oryza sativa",
            "Zea mays",
            "Glycine max",
            "Vitis vinifera",
            "Populus trichocarpa",
            "Sorghum bicolor",
            "Brassica rapa",
            "Medicago truncatula"
        ]
        input_species_file.write_text("\n".join(species_list))
        logger.info(f"Created temporary species list at {input_species_file}")
    
    species_names = [line.strip() for line in stream_file_lines(input_species_file) if line.strip()]
    logger.info(f"Loaded {len(species_names)} species from {input_species_file}")
    assert len(species_names) > 0, "No species found in input file"

    # 2. Fetch Marker Genes (18S, rbcL, matK)
    # Note: In a real CI environment, this might be slow or fail due to NCBI limits.
    # The task requires REAL data. If fetch fails, it must raise ValueError.
    logger.info("Fetching marker genes...")
    try:
        # This calls the real implementation from data_loader
        # We expect this to fetch real sequences or fail loudly
        gene_data = fetch_marker_genes(species_names, loci=["18S", "rbcL", "matK"])
        save_fasta_sequences(gene_data, PROJECT_ROOT / "data/raw/concatenated_test.fasta")
    except ValueError as e:
        logger.error(f"Data fetch failed: {e}")
        # If real data fetch fails, the test fails. No synthetic fallback.
        raise

    # 3. Fetch Metabolite Profiles (KEGG)
    logger.info("Fetching metabolite profiles...")
    metab_data = fetch_metabolite_profiles(species_names)
    
    # Filter species that have both sequence and metabolite data
    valid_species = [s for s in species_names if s in gene_data and s in metab_data]
    if len(valid_species) < 3:
        logger.error(f"Too few species with both data types: {len(valid_species)}")
        raise RuntimeError(f"Insufficient data: only {len(valid_species)} species have both sequence and metabolite profiles.")
    
    logger.info(f"Proceeding with {len(valid_species)} valid species")

    # 4. Concatenate Sequences
    logger.info("Concatenating sequences...")
    concat_fasta = PROJECT_ROOT / "data/raw/concatenated_test.fasta"
    if not concat_fasta.exists():
        # Fallback if the previous step didn't write to the expected path (implementation detail)
        # The fetch_marker_genes should have saved it, or we re-save.
        save_fasta_sequences(gene_data, concat_fasta)
    
    run_concatenation_pipeline(concat_fasta, PROJECT_ROOT / "data/raw/concatenated_test.fasta")

    # 5. Align Sequences (MAFFT)
    logger.info("Aligning sequences with MAFFT...")
    aligned_fasta = run_alignment_pipeline(PROJECT_ROOT / "data/raw/concatenated_test.fasta")

    # 6. Build Tree (FastTree)
    logger.info("Building phylogenetic tree with FastTree...")
    run_tree_building_pipeline(aligned_fasta, output_tree_file)
    
    assert output_tree_file.exists(), "Output tree file was not created"
    logger.info(f"Tree saved to {output_tree_file}")

    # 7. Calculate Phylogenetic Distance Matrix
    logger.info("Calculating patristic distance matrix...")
    phylo_dist_matrix = calculate_patristic_distance_matrix(output_tree_file, valid_species)
    phylo_dist_file = PROJECT_ROOT / "data/processed/test_phylo_dist_matrix.csv"
    phylo_dist_matrix.to_csv(phylo_dist_file)
    logger.info(f"Phylogenetic distance matrix saved to {phylo_dist_file}")

    # 8. Calculate Metabolite Dissimilarity Matrix (Jaccard)
    logger.info("Calculating metabolite dissimilarity matrix...")
    metab_dist_matrix = calculate_jaccard_dissimilarity_matrix(metab_data, valid_species)
    metab_dist_file = PROJECT_ROOT / "data/processed/test_metab_dist_matrix.csv"
    metab_dist_matrix.to_csv(metab_dist_file)
    logger.info(f"Metabolite distance matrix saved to {metab_dist_file}")

    # 9. Run Mantel Test
    logger.info("Running Mantel test...")
    # Use 999 permutations for small sample size (standard for small datasets)
    mantel_result = run_mantel_test(
        phylo_dist_matrix, 
        metab_dist_matrix, 
        permutations=999, 
        method="spearman"
    )
    
    # Save results
    result_dict = {
        "r": float(mantel_result["r"]),
        "p_value": float(mantel_result["p_value"]),
        "permutations": mantel_result["permutations"],
        "method": mantel_result["method"],
        "species_count": len(valid_species)
    }
    with open(output_mantel_file, "w") as f:
        json.dump(result_dict, f, indent=2)
    
    logger.info(f"Mantel Test Results: r={result_dict['r']:.4f}, p={result_dict['p_value']:.4f}")

    # 10. Log Validation (SC-001)
    p_val = result_dict["p_value"]
    # Threshold: < 0.05 for standard, < 0.1 for small sample (N=10 is small)
    threshold = 0.1 if len(valid_species) <= 10 else 0.05
    status = "PASS" if p_val < threshold else "FAIL"
    log_entry = f"SC-001: p={p_val:.4f} (Threshold={threshold}) -> {status}"
    append_validation_log(log_entry)
    
    logger.info(f"Validation log entry: {log_entry}")

    # 11. Assertion
    # The task requires p-value < 0.05 (or < 0.1 for small sample)
    assert p_val < threshold, (
        f"Mantel test p-value ({p_val:.4f}) is not significant (threshold: {threshold}). "
        "Phylogenetic signal may not be detectable in this dataset or sample size."
    )

    logger.info("Integration test PASSED: Full pipeline executed successfully with significant phylogenetic signal.")

if __name__ == "__main__":
    test_full_pipeline_run()
