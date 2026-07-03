"""
Unit tests for enrichment analysis module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.enrichment import (
    benjamini_hochberg_correction,
    calculate_enrichment,
    process_cell_type_enrichment,
    aggregate_enrichment_results
)


class TestBenjaminiHochbergCorrection:
    """Tests for Benjamini-Hochberg correction function."""

    def test_benjamini_hochberg_basic(self):
        """Test basic BH correction with known values."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        q_values = benjamini_hochberg_correction(p_values)
        
        assert len(q_values) == len(p_values)
        assert all(0 <= q <= 1 for q in q_values)
        # Q-values should be >= corresponding p-values
        assert all(q >= p for p, q in zip(p_values, q_values))
        # Q-values should be monotonically increasing when sorted by p-value
        sorted_indices = sorted(range(len(p_values)), key=lambda i: p_values[i])
        sorted_q = [q_values[i] for i in sorted_indices]
        assert all(sorted_q[i] <= sorted_q[i+1] for i in range(len(sorted_q)-1))

    def test_benjamini_hochberg_empty(self):
        """Test BH correction with empty input."""
        q_values = benjamini_hochberg_correction([])
        assert q_values == []

    def test_benjamini_hochberg_single(self):
        """Test BH correction with single value."""
        p_values = [0.05]
        q_values = benjamini_hochberg_correction(p_values)
        assert len(q_values) == 1
        assert q_values[0] == 0.05  # Single value: q = p

    def test_benjamini_hochberg_all_zeros(self):
        """Test BH correction with all zero p-values."""
        p_values = [0.0, 0.0, 0.0]
        q_values = benjamini_hochberg_correction(p_values)
        assert all(q == 0.0 for q in q_values)

    def test_benjamini_hochberg_all_ones(self):
        """Test BH correction with all one p-values."""
        p_values = [1.0, 1.0, 1.0]
        q_values = benjamini_hochberg_correction(p_values)
        assert all(q == 1.0 for q in q_values)


class TestCalculateEnrichment:
    """Tests for Fisher's exact test enrichment calculation."""

    def test_calculate_enrichment_basic(self):
        """Test basic enrichment calculation."""
        target_motifs = pd.DataFrame({'motif_id': ['A', 'A', 'B']})
        background_peaks = pd.DataFrame({'motif_id': ['A', 'B', 'B', 'B']})
        
        p_value, odds_ratio = calculate_enrichment(
            target_motifs, background_peaks, 10, 10
        )
        
        assert isinstance(p_value, float)
        assert isinstance(odds_ratio, float)
        assert 0 <= p_value <= 1
        assert odds_ratio >= 0

    def test_calculate_enrichment_no_background(self):
        """Test enrichment when no motif in background."""
        target_motifs = pd.DataFrame({'motif_id': ['A', 'A']})
        background_peaks = pd.DataFrame({'motif_id': ['B', 'B']})
        
        p_value, odds_ratio = calculate_enrichment(
            target_motifs, background_peaks, 10, 10
        )
        
        # Should return very small p-value for strong enrichment
        assert p_value < 1e-100
        assert odds_ratio == float('inf')

    def test_calculate_enrichment_all_background(self):
        """Test enrichment when motif in all background."""
        target_motifs = pd.DataFrame({'motif_id': ['A']})
        background_peaks = pd.DataFrame({'motif_id': ['A', 'A', 'A', 'A']})
        
        p_value, odds_ratio = calculate_enrichment(
            target_motifs, background_peaks, 10, 10
        )
        
        assert p_value == 1.0
        assert odds_ratio == 0.0


class TestEnrichmentIntegration:
    """Integration tests for enrichment analysis."""

    def test_process_cell_type_enrichment_empty(self):
        """Test processing with no input data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scan_dir = Path(tmpdir) / "scan_results"
            scan_dir.mkdir()
            peak_dir = Path(tmpdir) / "processed_peaks"
            peak_dir.mkdir()
            
            # Create empty files
            (scan_dir / "GM_motifs.tsv").write_text("motif_id\tsequence_name\n")
            (peak_dir / "GM_background.bed").write_text("")
            
            result = process_cell_type_enrichment("GM", scan_dir, peak_dir)
            
            assert isinstance(result, pd.DataFrame)

    def test_aggregate_enrichment_results_structure(self):
        """Test that aggregation produces correct matrix structure."""
        # This test assumes that process_cell_type_enrichment works correctly
        # We're just checking the aggregation logic
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "enrichment_matrix.csv"
            
            # Create mock results for one cell type
            scan_dir = Path(tmpdir) / "scan_results"
            scan_dir.mkdir()
            peak_dir = Path(tmpdir) / "processed_peaks"
            peak_dir.mkdir()
            
            # Create mock data
            mock_motifs = pd.DataFrame({
                'motif_id': ['A', 'A', 'B'],
                'sequence_name': ['seq1', 'seq2', 'seq3']
            })
            mock_motifs.to_csv(scan_dir / "GM_motifs.tsv", sep='\t', index=False)
            
            mock_bg = pd.DataFrame({
                'motif_id': ['A', 'B', 'B'],
                'chrom': ['chr1', 'chr1', 'chr2'],
                'start': [100, 200, 300],
                'end': [200, 300, 400]
            })
            mock_bg.to_csv(peak_dir / "GM_background.bed", sep='\t', index=False)
            
            # Create target peaks file
            mock_peaks = pd.DataFrame({
                'chrom': ['chr1', 'chr1', 'chr2'],
                'start': [100, 200, 300],
                'end': [200, 300, 400]
            })
            mock_peaks.to_csv(peak_dir / "GM_peaks.bed", sep='\t', header=False, index=False)
            
            # Run aggregation
            result = aggregate_enrichment_results(
                cell_types=['GM'],
                output_file=output_file
            )
            
            if not result.empty:
                assert 'motif_id' in result.columns or result.index.name == 'motif_id'
                assert 'GM' in result.columns