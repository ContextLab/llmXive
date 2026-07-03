import pytest
import csv
import os
import tempfile
from pathlib import Path
import sys

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from data.validate_labels import calculate_cohen_kappa, load_manual_labels, validate_disclosure_signal

class TestCohenKappa:
    def test_perfect_agreement(self):
        """Test Kappa = 1.0 for perfect agreement."""
        pred = ['Disclosing', 'Non-Disclosing', 'Disclosing']
        actual = ['Disclosing', 'Non-Disclosing', 'Disclosing']
        kappa = calculate_cohen_kappa(pred, actual)
        assert abs(kappa - 1.0) < 1e-6

    def test_chance_agreement(self):
        """Test Kappa ~ 0.0 for random agreement (approx)."""
        # Construct a case where agreement is purely by chance
        # e.g., 50% class A, 50% class B, but they don't align
        # This is hard to construct manually for exact 0, but we test a known case
        # Case: Pred=[A, A], Actual=[B, B] -> Po=0, Pe=0.5 -> Kappa = -1.0
        pred = ['A', 'A']
        actual = ['B', 'B']
        kappa = calculate_cohen_kappa(pred, actual)
        # Po = 0/2 = 0
        # Pe = (1.0 * 0.0) + (0.0 * 1.0) = 0 -> Wait, class counts:
        # A: pred=2, actual=0. B: pred=0, actual=2.
        # Pe = (2/2 * 0/2) + (0/2 * 2/2) = 0.
        # Kappa = (0 - 0) / (1 - 0) = 0.
        # Let's try a different case for Pe > 0.
        # Pred: [A, A, B, B], Actual: [A, B, A, B]
        # Po = 2/4 = 0.5
        # A: pred=2, actual=2. B: pred=2, actual=2.
        # Pe = (0.5 * 0.5) + (0.5 * 0.5) = 0.5
        # Kappa = (0.5 - 0.5) / (1 - 0.5) = 0.
        pred = ['A', 'A', 'B', 'B']
        actual = ['A', 'B', 'A', 'B']
        kappa = calculate_cohen_kappa(pred, actual)
        assert abs(kappa - 0.0) < 1e-6

    def test_empty_lists(self):
        """Test handling of empty lists."""
        kappa = calculate_cohen_kappa([], [])
        assert kappa == 0.0

    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise an error."""
        with pytest.raises(ValueError):
            calculate_cohen_kappa(['A', 'B'], ['A'])

class TestLoadManualLabels:
    def test_load_valid_csv(self):
        """Test loading a valid manual labels CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['pr_number', 'manual_label'])
            writer.writerow([1, 'Disclosing'])
            writer.writerow([2, 'Non-Disclosing'])
            temp_path = f.name

        try:
            labels = load_manual_labels(temp_path)
            assert labels[1] == 'Disclosing'
            assert labels[2] == 'Non-Disclosing'
        finally:
            os.unlink(temp_path)

    def test_load_missing_file(self):
        """Test loading a non-existent file returns empty dict."""
        labels = load_manual_labels("non_existent_file.csv")
        assert labels == {}

    def test_load_invalid_labels(self):
        """Test that invalid labels are skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['pr_number', 'manual_label'])
            writer.writerow([1, 'Disclosing'])
            writer.writerow([2, 'InvalidLabel'])
            temp_path = f.name

        try:
            labels = load_manual_labels(temp_path)
            assert 1 in labels
            assert 2 not in labels
        finally:
            os.unlink(temp_path)
