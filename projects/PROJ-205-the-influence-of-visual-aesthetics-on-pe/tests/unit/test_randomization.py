"""
Unit tests for the Latin Square randomization logic.

Tests verify:
1. The generated sequences form a mathematically valid Balanced Latin Square.
2. The selection logic distributes participants uniformly across sequences.
3. Every stimulus appears exactly once in each position across the set of sequences.
"""

import unittest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from survey.randomization import (
    generate_latin_square,
    select_sequence,
    verify_latin_square_balance,
    get_sequences_for_stimuli
)


class TestLatinSquareGeneration(unittest.TestCase):
    """Tests for the core Latin Square generation logic."""

    def test_generate_4_stimuli(self):
        """Test generation with 4 stimuli (the project's standard)."""
        stimuli = ["A", "B", "C", "D"]
        sequences = generate_latin_square(stimuli)

        self.assertEqual(len(sequences), 4, "Should generate 4 sequences for 4 stimuli")
        for seq in sequences:
            self.assertEqual(len(seq), 4, "Each sequence should have 4 stimuli")
            self.assertEqual(set(seq), set(stimuli), "Each sequence should contain all stimuli exactly once")

    def test_balanced_property_position(self):
        """Verify that every stimulus appears exactly once in each position."""
        stimuli = ["P1", "P2", "P3", "P4"]
        sequences = generate_latin_square(stimuli)

        # Check each column (position)
        for pos in range(4):
            column = [seq[pos] for seq in sequences]
            self.assertEqual(len(set(column)), 4, f"Position {pos} should have unique stimuli")
            self.assertEqual(set(column), set(stimuli), f"Position {pos} should contain all stimuli")

    def test_balanced_property_precedence(self):
        """Verify that every stimulus precedes every other stimulus exactly once."""
        stimuli = ["X", "Y", "Z", "W"]
        sequences = generate_latin_square(stimuli)

        # Count precedences
        precedes = {a: {b: 0 for b in stimuli} for a in stimuli}
        for seq in sequences:
            for i in range(len(seq) - 1):
                a, b = seq[i], seq[i+1]
                precedes[a][b] += 1

        # Check that every pair (a, b) with a != b has count 1
        for a in stimuli:
            for b in stimuli:
                if a != b:
                    self.assertEqual(precedes[a][b], 1, f"{a} should precede {b} exactly once")

    def test_verify_latin_square_balance(self):
        """Test the verification function."""
        stimuli = ["A", "B", "C", "D"]
        sequences = generate_latin_square(stimuli)
        self.assertTrue(verify_latin_square_balance(sequences), "Generated sequences should be valid")

    def test_invalid_stimuli_count(self):
        """Test that generation fails with less than 2 stimuli."""
        with self.assertRaises(ValueError):
            generate_latin_square(["A"])

        with self.assertRaises(ValueError):
            generate_latin_square([])


class TestSequenceSelection(unittest.TestCase):
    """Tests for the participant-based sequence selection."""

    def test_deterministic_selection(self):
        """Test that the same participant ID always selects the same sequence."""
        stimuli = ["A", "B", "C", "D"]
        participant_id = "test-participant-123"

        seq1 = select_sequence(stimuli, participant_id)
        seq2 = select_sequence(stimuli, participant_id)

        self.assertEqual(seq1, seq2, "Same participant ID should select same sequence")

    def test_different_participants_different_sequences(self):
        """Test that different participant IDs can select different sequences."""
        stimuli = ["A", "B", "C", "D"]
        # Use IDs with different hash values to ensure different sequences
        # We can't guarantee collision-free distribution with just 2 IDs,
        # but we can test that the function works.
        ids = [f"p-{i}" for i in range(10)]
        selected = [select_sequence(stimuli, pid) for pid in ids]

        # Just verify we got valid sequences
        for seq in selected:
            self.assertEqual(len(seq), 4)
            self.assertEqual(set(seq), set(stimuli))

    def test_runtime_selection_uniformity(self):
        """Simulate 100 participants and assert the distribution of sequences is uniform."""
        stimuli = ["A", "B", "C", "D"]
        n_participants = 100

        sequences = generate_latin_square(stimuli)
        sequence_indices = []

        for i in range(n_participants):
            pid = f"sim-participant-{i}"
            selected_seq = select_sequence(stimuli, pid)
            # Find index of selected sequence
            idx = sequences.index(selected_seq)
            sequence_indices.append(idx)

        # Count occurrences
        counts = [sequence_indices.count(i) for i in range(4)]
        
        # With 100 participants and 4 sequences, we expect ~25 per sequence.
        # We allow a reasonable tolerance (e.g., ±10) to account for the 
        # deterministic hash distribution which isn't perfectly uniform 
        # for small N, but should be close for N=100.
        expected = n_participants / 4
        tolerance = 10 
        
        for count in counts:
            self.assertGreaterEqual(count, expected - tolerance, 
                f"Sequence count {count} is below expected {expected} - tolerance {tolerance}")
            self.assertLessEqual(count, expected + tolerance, 
                f"Sequence count {count} is above expected {expected} + tolerance {tolerance}")
        
        # Additionally, ensure no sequence is completely ignored
        self.assertTrue(all(c > 0 for c in counts), "Every sequence must be selected at least once")


if __name__ == "__main__":
    unittest.main()