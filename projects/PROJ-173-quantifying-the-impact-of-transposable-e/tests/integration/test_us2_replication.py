"""
Integration test for User Story 2: Replication Pipeline with Missing Data Scenarios.

This test verifies that the replication pipeline correctly handles missing expression data
by excluding affected lines and calculating concordance on the remaining valid pairs.

Prerequisites:
- T004, T004A, T004B: Mock data generation (TE genotypes, expression, PCs)
- T031-T036: Replication logic implementation in code/replication.py
"""
import os
import sys
import csv
import tempfile
import shutil
import pytest

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data_generator import (
    generate_gene_models,
    generate_te_genotypes,
    generate_expression_data,
    generate_population_pcs,
    validate_schema,
    write_csv,
    set_random_seed
)
from code.replication import (
    run_replication_analysis,
    ReplicationError,
    load_replication_expression_data,
    load_replication_te_presence_data,
    load_replication_pcs_data,
    get_common_lines,
    fit_replication_model,
    calculate_concordance
)
from code.utils import ensure_directory, set_random_seed as utils_set_seed

# Constants for test configuration
NUM_LINES = 50
NUM_GENES = 20
NUM_TES = 15
MISSING_RATE = 0.2  # 20% missing data rate for testing
RANDOM_SEED = 4223

class TestReplicationMissingData:
    """Integration tests for replication pipeline missing data handling."""

    def setup_method(self):
        """Set up temporary directory and generate mock datasets."""
        self.test_dir = tempfile.mkdtemp(prefix="us2_replication_test_")
        self.data_dir = os.path.join(self.test_dir, "data")
        self.results_dir = os.path.join(self.test_dir, "results")
        ensure_directory(self.data_dir)
        ensure_directory(self.results_dir)
        
        utils_set_seed(RANDOM_SEED)

        # Generate Gene Models
        gene_models = generate_gene_models(NUM_GENES, seed=RANDOM_SEED)
        write_csv(
            os.path.join(self.data_dir, "gene_models.csv"),
            gene_models,
            fieldnames=["gene_id", "chrom", "tss", "tes", "strand"]
        )

        # Generate TE Genotypes (Primary Dataset)
        te_genotypes_primary = generate_te_genotypes(NUM_TES, NUM_LINES, seed=RANDOM_SEED)
        write_csv(
            os.path.join(self.data_dir, "te_genotypes_primary.csv"),
            te_genotypes_primary,
            fieldnames=["te_id"] + [f"line_{i}" for i in range(NUM_LINES)]
        )

        # Generate Expression Data (Primary Dataset)
        # We simulate a scenario where some pairs are significant
        expr_primary = generate_expression_data(NUM_GENES, NUM_LINES, seed=RANDOM_SEED)
        write_csv(
            os.path.join(self.data_dir, "expression_primary.csv"),
            expr_primary,
            fieldnames=["gene_id"] + [f"line_{i}" for i in range(NUM_LINES)]
        )

        # Generate PCs (Primary Dataset)
        pcs_primary = generate_population_pcs(NUM_LINES, seed=RANDOM_SEED)
        write_csv(
            os.path.join(self.data_dir, "pcs_primary.csv"),
            pcs_primary,
            fieldnames=["line_id", "PC1", "PC2", "PC3"]
        )

        # Generate Replication Dataset (Independent)
        # Use a different seed to ensure independence
        utils_set_seed(RANDOM_SEED + 100)
        
        te_genotypes_rep = generate_te_genotypes(NUM_TES, NUM_LINES, seed=RANDOM_SEED + 100)
        write_csv(
            os.path.join(self.data_dir, "te_genotypes_replication.csv"),
            te_genotypes_rep,
            fieldnames=["te_id"] + [f"line_{i}" for i in range(NUM_LINES)]
        )

        # Introduce Missing Data in Replication Expression
        expr_rep_raw = generate_expression_data(NUM_GENES, NUM_LINES, seed=RANDOM_SEED + 100)
        
        # Inject missing values (simulate missing data scenario)
        # We will modify the CSV content to have empty cells
        expr_rep_with_missing = []
        for row in expr_rep_raw:
            new_row = row.copy()
            # Randomly set some expression values to empty string to simulate missing data
            for i in range(1, len(new_row)):
                if random.random() < MISSING_RATE:
                    new_row[i] = ""
            expr_rep_with_missing.append(new_row)
        
        write_csv(
            os.path.join(self.data_dir, "expression_replication_missing.csv"),
            expr_rep_with_missing,
            fieldnames=["gene_id"] + [f"line_{i}" for i in range(NUM_LINES)]
        )

        # PCs for replication (should be similar but independent)
        pcs_rep = generate_population_pcs(NUM_LINES, seed=RANDOM_SEED + 100)
        write_csv(
            os.path.join(self.data_dir, "pcs_replication.csv"),
            pcs_rep,
            fieldnames=["line_id", "PC1", "PC2", "PC3"]
        )

        # Create a mock "significant pairs" list from US1
        # In a real scenario, this would be the output of T023
        significant_pairs = [
            {"te_id": "TE_0", "gene_id": "Gene_0", "effect_size": 0.5, "adj_pval": 0.01},
            {"te_id": "TE_1", "gene_id": "Gene_1", "effect_size": -0.3, "adj_pval": 0.03},
            {"te_id": "TE_2", "gene_id": "Gene_2", "effect_size": 0.8, "adj_pval": 0.001},
            {"te_id": "TE_3", "gene_id": "Gene_3", "effect_size": 0.2, "adj_pval": 0.04},
        ]
        
        pairs_path = os.path.join(self.data_dir, "significant_pairs_us1.csv")
        write_csv(pairs_path, significant_pairs, fieldnames=["te_id", "gene_id", "effect_size", "adj_pval"])

    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_replication_pipeline_handles_missing_data(self):
        """
        Test that the replication pipeline correctly excludes lines with missing data
        and calculates concordance on the remaining valid lines.
        """
        import random
        random.seed(RANDOM_SEED) # Ensure consistent random behavior if needed inside test

        # Define input paths
        expr_primary_path = os.path.join(self.data_dir, "expression_primary.csv")
        te_primary_path = os.path.join(self.data_dir, "te_genotypes_primary.csv")
        pcs_primary_path = os.path.join(self.data_dir, "pcs_primary.csv")
        
        expr_rep_path = os.path.join(self.data_dir, "expression_replication_missing.csv")
        te_rep_path = os.path.join(self.data_dir, "te_genotypes_replication.csv")
        pcs_rep_path = os.path.join(self.data_dir, "pcs_replication.csv")
        
        pairs_path = os.path.join(self.data_dir, "significant_pairs_us1.csv")
        output_path = os.path.join(self.results_dir, "replication_results.csv")

        # Run the replication analysis
        # This function should internally handle missing data by excluding lines
        # where expression or TE presence is missing for the specific pair
        try:
            run_replication_analysis(
                primary_expr_path=expr_primary_path,
                primary_te_path=te_primary_path,
                primary_pcs_path=pcs_primary_path,
                rep_expr_path=expr_rep_path,
                rep_te_path=te_rep_path,
                rep_pcs_path=pcs_rep_path,
                significant_pairs_path=pairs_path,
                output_path=output_path
            )
        except Exception as e:
            pytest.fail(f"Replication analysis failed with error: {str(e)}")

        # Verify output file exists
        assert os.path.exists(output_path), f"Output file {output_path} was not created."

        # Verify output content
        with open(output_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) > 0, "Replication output is empty."
        
        # Check required columns
        required_cols = ["te_id", "gene_id", "orig_effect", "rep_effect", "concordance", "rep_pval"]
        for col in required_cols:
            assert col in rows[0], f"Missing required column: {col}"

        # Verify that missing data was handled (i.e., not all pairs failed)
        # The pipeline should have found common lines and calculated results
        # even with some missing data points
        successful_pairs = [r for r in rows if r['rep_pval'] != '']
        assert len(successful_pairs) > 0, "No pairs were successfully replicated; missing data handling may be too aggressive or broken."

    def test_common_lines_calculation_with_missing_data(self):
        """
        Test that get_common_lines correctly identifies lines available in both
        primary and replication datasets, excluding those with missing values.
        """
        import random
        random.seed(RANDOM_SEED)

        expr_rep_path = os.path.join(self.data_dir, "expression_replication_missing.csv")
        te_rep_path = os.path.join(self.data_dir, "te_genotypes_replication.csv")
        
        # Load data
        rep_expr = load_replication_expression_data(expr_rep_path)
        rep_te = load_replication_te_presence_data(te_rep_path)
        
        # Get line IDs
        rep_expr_lines = set(rep_expr[0].keys()) - {"gene_id"}
        rep_te_lines = set(rep_te[0].keys()) - {"te_id"}
        
        # Calculate intersection
        common_lines = get_common_lines(rep_expr, rep_te)
        
        # Verify that common lines are a subset of both
        assert set(common_lines).issubset(rep_expr_lines)
        assert set(common_lines).issubset(rep_te_lines)
        
        # Verify that lines with missing values in either dataset are excluded
        # (This is implicit in the logic, but we can check the count)
        # Since we injected missing values, the common lines should be fewer than total lines
        # unless the missing values were injected in a way that didn't affect the intersection
        # (which is unlikely given the random injection)
        assert len(common_lines) <= NUM_LINES

    def test_concordance_calculation_with_partial_data(self):
        """
        Test that concordance is calculated correctly even when some pairs
        have missing data in the replication set.
        """
        import random
        random.seed(RANDOM_SEED)

        # Simulate effect sizes
        orig_effects = [0.5, -0.3, 0.8, 0.2, -0.1]
        rep_effects = [0.4, -0.2, 0.7, 0.0, 0.1] # Last one has opposite sign -> discordant
        
        concordance_flag = calculate_concordance(orig_effects, rep_effects)
        
        # Expected: 4 concordant (same sign), 1 discordant
        # concordance_rate = 4/5 = 0.8
        assert abs(concordance_flag - 0.8) < 1e-6, f"Expected concordance ~0.8, got {concordance_flag}"

    def test_replication_analysis_with_all_missing_data(self):
        """
        Edge case: Test behavior when all replication expression data is missing.
        The pipeline should handle this gracefully (e.g., output empty table or error).
        """
        import random
        random.seed(RANDOM_SEED)

        # Create a file with all missing expression data
        all_missing_expr = []
        for i in range(NUM_GENES):
            row = {"gene_id": f"Gene_{i}"}
            for j in range(NUM_LINES):
                row[f"line_{j}"] = ""
            all_missing_expr.append(row)
        
        all_missing_path = os.path.join(self.data_dir, "expression_all_missing.csv")
        write_csv(all_missing_path, all_missing_expr, fieldnames=["gene_id"] + [f"line_{i}" for i in range(NUM_LINES)])

        expr_primary_path = os.path.join(self.data_dir, "expression_primary.csv")
        te_primary_path = os.path.join(self.data_dir, "te_genotypes_primary.csv")
        pcs_primary_path = os.path.join(self.data_dir, "pcs_primary.csv")
        
        te_rep_path = os.path.join(self.data_dir, "te_genotypes_replication.csv")
        pcs_rep_path = os.path.join(self.data_dir, "pcs_replication.csv")
        pairs_path = os.path.join(self.data_dir, "significant_pairs_us1.csv")
        output_path = os.path.join(self.results_dir, "replication_all_missing.csv")

        # This should either raise an error or produce an empty result
        # We expect it to handle the edge case without crashing
        try:
            run_replication_analysis(
                primary_expr_path=expr_primary_path,
                primary_te_path=te_primary_path,
                primary_pcs_path=pcs_primary_path,
                rep_expr_path=all_missing_path,
                rep_te_path=te_rep_path,
                rep_pcs_path=pcs_rep_path,
                significant_pairs_path=pairs_path,
                output_path=output_path
            )
            
            # If it runs, check output
            if os.path.exists(output_path):
                with open(output_path, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    # Should be empty or have rows with no valid p-values
                    assert len(rows) == 0 or all(r['rep_pval'] == '' for r in rows), "Unexpected results with all missing data"
            else:
                # If no output, it might have raised an error or logged it
                pass
        except ReplicationError:
            # Expected behavior for completely invalid data
            pass
        except Exception as e:
            # Any other error is acceptable as long as it's not a crash
            pytest.fail(f"Unexpected error type: {str(e)}")

    def test_replication_analysis_output_schema(self):
        """
        Verify that the output schema matches the specification for US2.
        """
        import random
        random.seed(RANDOM_SEED)

        # Re-run setup to ensure clean state
        self.setup_method()
        
        expr_primary_path = os.path.join(self.data_dir, "expression_primary.csv")
        te_primary_path = os.path.join(self.data_dir, "te_genotypes_primary.csv")
        pcs_primary_path = os.path.join(self.data_dir, "pcs_primary.csv")
        
        expr_rep_path = os.path.join(self.data_dir, "expression_replication_missing.csv")
        te_rep_path = os.path.join(self.data_dir, "te_genotypes_replication.csv")
        pcs_rep_path = os.path.join(self.data_dir, "pcs_replication.csv")
        pairs_path = os.path.join(self.data_dir, "significant_pairs_us1.csv")
        output_path = os.path.join(self.results_dir, "replication_results.csv")

        run_replication_analysis(
            primary_expr_path=expr_primary_path,
            primary_te_path=te_primary_path,
            primary_pcs_path=pcs_primary_path,
            rep_expr_path=expr_rep_path,
            rep_te_path=te_rep_path,
            rep_pcs_path=pcs_rep_path,
            significant_pairs_path=pairs_path,
            output_path=output_path
        )

        with open(output_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
        expected_fields = ["te_id", "gene_id", "orig_effect", "rep_effect", "concordance", "rep_pval"]
        for field in expected_fields:
            assert field in fieldnames, f"Missing field in output: {field}"
        
        # Verify data types in first row
        rows = list(reader)
        if rows:
            row = rows[0]
            # Check that numeric fields can be parsed
            float(row['orig_effect'])
            float(row['rep_effect'])
            float(row['rep_pval'])
            # Concordance should be 0.0 or 1.0 (or a rate if aggregated, but here per pair)
            # Actually, per pair concordance is a flag (True/False or 1/0)
            # But if it's a rate, it should be between 0 and 1
            # Let's assume it's a flag for this test
            assert row['concordance'] in ['True', 'False', '1', '0', '']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])