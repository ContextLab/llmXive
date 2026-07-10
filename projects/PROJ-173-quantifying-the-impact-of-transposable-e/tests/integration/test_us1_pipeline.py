"""
Integration test for User Story 1: Full TE-Gene Association Pipeline on Mock Data.

This test verifies the end-to-end execution of the US1 pipeline:
1. Generates Mock Data (TE genotypes, Gene Expression, PCs, Gene Models).
2. Preprocesses data (filters monomorphic TEs, maps TEs to genes, handles missing data).
3. Runs Association Analysis (fits linear models, calculates VIF, applies FDR).
4. Validates output schema and statistical properties.

Dependencies:
- code/data_generator.py (Mock data generation)
- code/preprocessing.py (TE-Gene mapping, VIF calculation)
- code/association.py (Model fitting, FDR correction)
- code/utils.py (Logging, directory management)
"""

import os
import sys
import csv
import math
import random
import logging
import tempfile
import shutil

# Add project root to path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from code.data_generator import (
    generate_te_genotypes,
    generate_expression_data,
    generate_population_pcs,
    generate_gene_models,
    filter_monomorphic_tes,
    DataGenerationError
)
from code.preprocessing import (
    map_te_to_genes,
    filter_missing_expression,
    calculate_vif,
    generate_vif_report
)
from code.association import (
    run_full_association_analysis,
    apply_bh_correction,
    AssociationError,
    load_expression_data,
    load_te_presence_data,
    load_pcs_data
)
from code.utils import setup_logger, ensure_directory, set_random_seed

# Configure logging for the test
logger = setup_logger("test_us1_integration", level=logging.INFO)

# Constants for test
RANDOM_SEED = 42
NUM_LINES = 50
NUM_TES = 100
NUM_GENES = 80
NUM_PCS = 3
MIN_FREQ = 0.05
MAX_FREQ = 0.95
PROXIMAL_THRESHOLD_KB = 5.0

def test_full_us1_pipeline():
    """
    Runs the complete US1 pipeline on generated mock data and validates results.
    """
    logger.info("Starting US1 Integration Test...")
    
    # Create a temporary directory for test outputs
    test_dir = tempfile.mkdtemp(prefix="us1_test_")
    data_dir = os.path.join(test_dir, "data")
    results_dir = os.path.join(data_dir, "results")
    ensure_directory(results_dir)

    try:
        set_random_seed(RANDOM_SEED)

        # --- Step 1: Generate Mock Data ---
        logger.info("Step 1: Generating Mock Data...")
        
        # 1a. TE Genotypes
        te_file = os.path.join(data_dir, "te_genotypes_raw.csv")
        generate_te_genotypes(
            output_path=te_file,
            num_lines=NUM_LINES,
            num_tes=NUM_TES,
            min_freq=MIN_FREQ,
            max_freq=MAX_FREQ,
            seed=RANDOM_SEED
        )
        logger.info(f"Generated TE genotypes: {te_file}")

        # 1b. Gene Expression
        expr_file = os.path.join(data_dir, "gene_expression.csv")
        generate_expression_data(
            output_path=expr_file,
            num_lines=NUM_LINES,
            num_genes=NUM_GENES,
            seed=RANDOM_SEED
        )
        logger.info(f"Generated Gene Expression: {expr_file}")

        # 1c. Population PCs
        pcs_file = os.path.join(data_dir, "population_pcs.csv")
        generate_population_pcs(
            output_path=pcs_file,
            num_lines=NUM_LINES,
            num_pcs=NUM_PCS,
            seed=RANDOM_SEED
        )
        logger.info(f"Generated Population PCs: {pcs_file}")

        # 1d. Gene Models
        models_file = os.path.join(data_dir, "gene_models.csv")
        generate_gene_models(
            output_path=models_file,
            num_genes=NUM_GENES,
            seed=RANDOM_SEED
        )
        logger.info(f"Generated Gene Models: {models_file}")

        # --- Step 2: Preprocessing ---
        logger.info("Step 2: Preprocessing Data...")

        # 2a. Filter Monomorphic TEs
        te_filtered_file = os.path.join(data_dir, "te_genotypes_filtered.csv")
        filter_monomorphic_tes(
            input_path=te_file,
            output_path=te_filtered_file,
            min_freq=MIN_FREQ,
            max_freq=MAX_FREQ
        )
        logger.info(f"Filtered TE genotypes: {te_filtered_file}")

        # 2b. Map TEs to Genes
        pairs_file = os.path.join(data_dir, "te_gene_pairs.csv")
        map_te_to_genes(
            te_path=te_filtered_file,
            gene_models_path=models_file,
            output_path=pairs_file,
            proximal_threshold_kb=PROXIMAL_THRESHOLD_KB
        )
        logger.info(f"Mapped TE-Gene pairs: {pairs_file}")

        # 2c. Handle Missing Expression Data
        # (This step typically filters lines from the expression/TE/PC tables)
        # For this integration test, we assume the generator produced complete data,
        # but we call the function to ensure the pipeline path is exercised.
        expr_clean_file = os.path.join(data_dir, "gene_expression_clean.csv")
        filter_missing_expression(
            expr_path=expr_file,
            te_path=te_filtered_file,
            pcs_path=pcs_file,
            output_expr=expr_clean_file,
            output_te=os.path.join(data_dir, "te_genotypes_clean.csv"),
            output_pcs=os.path.join(data_dir, "pcs_clean.csv")
        )
        logger.info("Completed missing data filtering.")

        # --- Step 3: Association Analysis ---
        logger.info("Step 3: Running Association Analysis...")

        # Load cleaned data for analysis
        # Note: The analysis function expects paths to the cleaned files
        output_results = os.path.join(results_dir, "association_results.csv")
        vif_report = os.path.join(results_dir, "vif_report.csv")

        # Run the full analysis pipeline
        # This internally loads data, fits models, calculates VIF, and applies BH correction
        run_full_association_analysis(
            expr_path=expr_clean_file,
            te_path=os.path.join(data_dir, "te_genotypes_clean.csv"),
            pcs_path=os.path.join(data_dir, "pcs_clean.csv"),
            pairs_path=pairs_file,
            output_path=output_results,
            vif_output_path=vif_report,
            vif_threshold=5.0
        )

        logger.info(f"Association analysis complete. Results: {output_results}")

        # --- Step 4: Validation ---
        logger.info("Step 4: Validating Results...")

        # Check 4a: Output file exists and is not empty
        assert os.path.exists(output_results), f"Output file not found: {output_results}"
        with open(output_results, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) > 0, "Association results are empty. Expected at least some pairs."
        logger.info(f"Found {len(rows)} association results.")

        # Check 4b: Schema validation (required columns)
        required_columns = [
            'te_id', 'gene_id', 'distance_kb', 'effect_size', 
            'std_error', 'p_value', 'adj_p_value', 'vif_flag'
        ]
        if len(rows) > 0:
            actual_columns = rows[0].keys()
            for col in required_columns:
                assert col in actual_columns, f"Missing required column: {col}"
            logger.info("Schema validation passed.")

        # Check 4c: Statistical sanity
        # - adj_p_value should be between 0 and 1
        # - effect_size can be any float
        for row in rows:
            p_val = float(row['adj_p_value'])
            assert 0.0 <= p_val <= 1.0, f"Invalid adj_p_value: {p_val}"
            
            vif_flag = row['vif_flag']
            assert vif_flag in ['PASS', 'FLAGGED'], f"Invalid vif_flag: {vif_flag}"

        logger.info("Statistical sanity checks passed.")

        # Check 4d: VIF Report exists
        assert os.path.exists(vif_report), f"VIF report not found: {vif_report}"
        with open(vif_report, 'r') as f:
            vif_rows = list(csv.DictReader(f))
        assert len(vif_rows) > 0, "VIF report is empty."
        logger.info("VIF report validation passed.")

        logger.info("✅ US1 Integration Test PASSED.")
        return True

    except DataGenerationError as e:
        logger.error(f"Data generation failed: {e}")
        raise
    except AssociationError as e:
        logger.error(f"Association analysis failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Integration test failed with unexpected error: {e}")
        raise
    finally:
        # Cleanup temporary directory
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            logger.info(f"Cleaned up temporary directory: {test_dir}")

if __name__ == "__main__":
    test_full_us1_pipeline()
    print("All integration tests passed successfully.")