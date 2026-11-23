"""
Unit tests for residual permutation logic in code/permutation.py.
Verifies null distribution generation and statistical properties.
"""
import os
import sys
import unittest
import math
import random
import csv
import tempfile
import shutil

# Add project root to path to allow imports from code/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.permutation import (
    PermutationError,
    compute_residuals,
    generate_null_distribution,
    compute_permutation_pvalue
)
from code.utils import set_random_seed

class TestPermutationLogic(unittest.TestCase):
    """Unit tests for the residual permutation module."""

    def setUp(self):
        """Set up test fixtures."""
        set_random_seed(42)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_mock_data_files(self, n_lines=50, n_genes=10):
        """Helper to create mock expression, TE, and PC data files."""
        expr_path = os.path.join(self.temp_dir, "mock_expression.csv")
        te_path = os.path.join(self.temp_dir, "mock_te_presence.csv")
        pc_path = os.path.join(self.temp_dir, "mock_pcs.csv")

        lines = [f"line_{i}" for i in range(n_lines)]
        genes = [f"gene_{i}" for i in range(n_genes)]
        tes = [f"TE_{i}" for i in range(5)]  # 5 TEs for testing

        # Generate mock expression data (TPM)
        with open(expr_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['line_id'] + genes)
            for line in lines:
                row = [line] + [random.uniform(0.1, 100.0) for _ in genes]
                writer.writerow(row)

        # Generate mock TE presence data (binary)
        with open(te_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['line_id', 'te_id'] + genes)
            for line in lines:
                for te in tes:
                    row = [line, te] + [random.randint(0, 1) for _ in genes]
                    writer.writerow(row)

        # Generate mock PCs
        with open(pc_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['line_id', 'PC1', 'PC2', 'PC3'])
            for line in lines:
                row = [line, random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1)]
                writer.writerow(row)

        return expr_path, te_path, pc_path, lines, genes, tes

    def test_compute_residuals_basic(self):
        """Test that residuals are computed correctly for a simple linear model."""
        # Create simple synthetic data
        lines = ["L1", "L2", "L3", "L4", "L5"]
        gene = "gene_1"
        te = "TE_1"
        
        expr_path = os.path.join(self.temp_dir, "expr.csv")
        te_path = os.path.join(self.temp_dir, "te.csv")
        pc_path = os.path.join(self.temp_dir, "pcs.csv")

        # Expression: y = 2 + 3*x1 + 4*x2 + noise
        # We'll use PCs as predictors
        with open(expr_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['line_id', gene])
            for i, line in enumerate(lines):
                y = 2.0 + 3.0 * (i % 2) + 4.0 * ((i + 1) % 2) + random.gauss(0, 0.5)
                writer.writerow([line, y])

        # TE presence (not used in null model, but required by function signature)
        with open(te_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['line_id', 'te_id', gene])
            for line in lines:
                writer.writerow([line, te, 1])

        # PCs as predictors for null model
        with open(pc_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['line_id', 'PC1', 'PC2', 'PC3'])
            for i, line in enumerate(lines):
                pc1 = float(i % 2)
                pc2 = float((i + 1) % 2)
                pc3 = random.gauss(0, 1)
                writer.writerow([line, pc1, pc2, pc3])

        # Compute residuals
        residuals = compute_residuals(
            expr_path=expr_path,
            te_path=te_path,
            pc_path=pc_path,
            gene_id=gene,
            te_id=te,
            lines=lines
        )

        self.assertEqual(len(residuals), len(lines))
        self.assertIsInstance(residuals, list)
        # Residuals should have mean close to 0
        self.assertAlmostEqual(sum(residuals) / len(residuals), 0.0, places=1)

    def test_compute_residuals_empty_result(self):
        """Test handling of missing data or invalid inputs."""
        # Create files with mismatched lines
        expr_path = os.path.join(self.temp_dir, "expr.csv")
        te_path = os.path.join(self.temp_dir, "te.csv")
        pc_path = os.path.join(self.temp_dir, "pcs.csv")

        with open(expr_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['line_id', 'gene_1'])
            writer.writerow(['L1', 10.0])
            writer.writerow(['L2', 20.0])

        with open(te_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['line_id', 'te_id', 'gene_1'])
            writer.writerow(['L1', 'TE_1', 1])

        with open(pc_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['line_id', 'PC1', 'PC2', 'PC3'])
            writer.writerow(['L3', 1.0, 1.0, 1.0])  # Mismatched line

        # Should raise PermutationError due to missing common lines
        with self.assertRaises(PermutationError):
            compute_residuals(
                expr_path=expr_path,
                te_path=te_path,
                pc_path=pc_path,
                gene_id='gene_1',
                te_id='TE_1',
                lines=['L1', 'L2', 'L3']
            )

    def test_generate_null_distribution(self):
        """Test that null distribution is generated with correct properties."""
        expr_path, te_path, pc_path, lines, genes, tes = self._create_mock_data_files(
            n_lines=30, n_genes=5
        )

        gene_id = genes[0]
        te_id = tes[0]
        n_permutations = 100

        null_dist = generate_null_distribution(
            expr_path=expr_path,
            te_path=te_path,
            pc_path=pc_path,
            gene_id=gene_id,
            te_id=te_id,
            lines=lines,
            n_permutations=n_permutations,
            random_seed=42
        )

        self.assertEqual(len(null_dist), n_permutations)
        self.assertIsInstance(null_dist, list)
        
        # Verify all values are numeric
        for val in null_dist:
            self.assertIsInstance(val, float)

        # With enough permutations, the distribution should be centered near 0
        # (since we're shuffling residuals under the null)
        mean_val = sum(null_dist) / len(null_dist)
        # Allow some tolerance due to random variation
        self.assertLess(abs(mean_val), 2.0, "Null distribution mean should be close to 0")

    def test_generate_null_distribution_deterministic(self):
        """Test that null distribution generation is deterministic with fixed seed."""
        expr_path, te_path, pc_path, lines, genes, tes = self._create_mock_data_files(
            n_lines=20, n_genes=3
        )

        gene_id = genes[0]
        te_id = tes[0]
        n_permutations = 50

        # Generate twice with same seed
        dist1 = generate_null_distribution(
            expr_path=expr_path,
            te_path=te_path,
            pc_path=pc_path,
            gene_id=gene_id,
            te_id=te_id,
            lines=lines,
            n_permutations=n_permutations,
            random_seed=123
        )

        dist2 = generate_null_distribution(
            expr_path=expr_path,
            te_path=te_path,
            pc_path=pc_path,
            gene_id=gene_id,
            te_id=te_id,
            lines=lines,
            n_permutations=n_permutations,
            random_seed=123
        )

        self.assertEqual(dist1, dist2, "Null distribution should be deterministic with fixed seed")

    def test_compute_permutation_pvalue(self):
        """Test p-value calculation from observed statistic and null distribution."""
        observed_t = 2.5
        null_dist = [1.2, 0.8, -0.5, 1.5, 2.0, -1.0, 0.3, 1.8, -0.2, 0.9]

        pvalue = compute_permutation_pvalue(observed_t, null_dist)

        # Count how many null values >= observed
        count = sum(1 for x in null_dist if x >= observed_t)
        expected_pvalue = count / len(null_dist)

        self.assertAlmostEqual(pvalue, expected_pvalue, places=6)
        self.assertGreaterEqual(pvalue, 0.0)
        self.assertLessEqual(pvalue, 1.0)

    def test_compute_permutation_pvalue_extreme_observed(self):
        """Test p-value when observed statistic is extreme."""
        # Observed is larger than all null values
        observed_t = 10.0
        null_dist = [1.2, 0.8, -0.5, 1.5, 2.0]

        pvalue = compute_permutation_pvalue(observed_t, null_dist)
        self.assertEqual(pvalue, 0.0)

        # Observed is smaller than all null values
        observed_t = -10.0
        pvalue = compute_permutation_pvalue(observed_t, null_dist)
        self.assertEqual(pvalue, 1.0)  # All null values are >= observed

    def test_null_distribution_shape(self):
        """Test that null distribution approximates expected shape with large N."""
        expr_path, te_path, pc_path, lines, genes, tes = self._create_mock_data_files(
            n_lines=100, n_genes=2
        )

        gene_id = genes[0]
        te_id = tes[0]
        n_permutations = 500

        null_dist = generate_null_distribution(
            expr_path=expr_path,
            te_path=te_path,
            pc_path=pc_path,
            gene_id=gene_id,
            te_id=te_id,
            lines=lines,
            n_permutations=n_permutations,
            random_seed=999
        )

        # Check basic statistical properties
        mean_val = sum(null_dist) / len(null_dist)
        variance = sum((x - mean_val) ** 2 for x in null_dist) / len(null_dist)

        # Mean should be close to 0
        self.assertLess(abs(mean_val), 1.5, "Null distribution mean should be near 0")
        
        # Variance should be positive and reasonable
        self.assertGreater(variance, 0.0, "Null distribution variance should be positive")
        self.assertLess(variance, 100.0, "Null distribution variance should be reasonable")

    def test_residual_permutation_preserves_structure(self):
        """Test that permutation shuffles residuals but preserves data structure."""
        expr_path, te_path, pc_path, lines, genes, tes = self._create_mock_data_files(
            n_lines=40, n_genes=4
        )

        gene_id = genes[0]
        te_id = tes[0]

        # Get original residuals
        original_residuals = compute_residuals(
            expr_path=expr_path,
            te_path=te_path,
            pc_path=pc_path,
            gene_id=gene_id,
            te_id=te_id,
            lines=lines
        )

        # Generate null distribution (which internally shuffles residuals)
        null_dist = generate_null_distribution(
            expr_path=expr_path,
            te_path=te_path,
            pc_path=pc_path,
            gene_id=gene_id,
            te_id=te_id,
            lines=lines,
            n_permutations=50,
            random_seed=42
        )

        # The null distribution values should be different from original residuals
        # (since they are derived from shuffled residuals)
        self.assertNotEqual(null_dist[0], 0.0)  # At least some variation expected

        # Verify that the set of values in null distribution comes from the same
        # underlying distribution as original residuals (same mean/variance roughly)
        orig_mean = sum(original_residuals) / len(original_residuals)
        orig_var = sum((x - orig_mean) ** 2 for x in original_residuals) / len(original_residuals)

        null_mean = sum(null_dist) / len(null_dist)
        null_var = sum((x - null_mean) ** 2 for x in null_dist) / len(null_dist)

        # Means should be close (both near 0)
        self.assertAlmostEqual(orig_mean, 0.0, places=1)
        self.assertAlmostEqual(null_mean, 0.0, places=1)

        # Variances should be comparable
        ratio = null_var / orig_var if orig_var > 0 else 1.0
        self.assertGreater(ratio, 0.5, "Null distribution variance should be comparable to original")
        self.assertLess(ratio, 2.0, "Null distribution variance should be comparable to original")

if __name__ == '__main__':
    unittest.main()