import pytest
from code.validate import validate_motifs
import numpy as np

def test_chip_overlap_calculation():
    """
    Test that overlap percentage is calculated correctly against a mock ChIP-seq dataset.
    Covers: US3-FR-005 (Validation against independent ChIP-seq data)
    
    This test verifies the overlap calculation logic using synthetic but
    structurally correct peak data.
    """
    # Mock predicted peaks (from our enrichment analysis)
    predicted_peaks = [
        {"chrom": "chr1", "start": 100, "end": 200, "motif": "MA0001"},
        {"chrom": "chr1", "start": 300, "end": 400, "motif": "MA0001"},
        {"chrom": "chr1", "start": 500, "end": 600, "motif": "MA0002"},
        {"chrom": "chr2", "start": "100", "end": 200, "motif": "MA0001"},
    ]
    
    # Mock ChIP-seq peaks (ground truth)
    chip_peaks = [
        {"chrom": "chr1", "start": 100, "end": 200},  # Exact match
        {"chrom": "chr1", "start": 310, "end": 390},  # Partial overlap
        {"chrom": "chr1", "start": 500, "end": 600},  # Exact match
        {"chrom": "chr3", "start": 100, "end": 200},  # No match
    ]
    
    # Calculate overlap
    overlap_pct = validate_motifs(predicted_peaks, chip_peaks, overlap_threshold=0.5)
    
    # Expected: 
    # - Peak 0 (100-200) overlaps with chip peak 0 (100-200) -> 100% overlap
    # - Peak 1 (300-400) overlaps with chip peak 1 (310-390) -> 80/100 = 80% overlap (threshold 0.5 met)
    # - Peak 2 (500-600) overlaps with chip peak 2 (500-600) -> 100% overlap
    # - Peak 3 (chr2 100-200) has no overlap (different chrom)
    # Overlap count: 3 out of 4 = 75%
    
    assert 0 <= overlap_pct <= 100, f"Overlap percentage {overlap_pct} should be in [0, 100]"
    assert overlap_pct == 75.0, f"Expected 75% overlap, got {overlap_pct}%"

def test_chip_overlap_no_matches():
    """
    Test overlap calculation when there are no matches.
    """
    predicted_peaks = [
        {"chrom": "chr1", "start": 100, "end": 200, "motif": "MA0001"},
    ]
    
    chip_peaks = [
        {"chrom": "chr2", "start": 100, "end": 200},  # Different chromosome
    ]
    
    overlap_pct = validate_motifs(predicted_peaks, chip_peaks)
    assert overlap_pct == 0.0, f"Expected 0% overlap, got {overlap_pct}%"

def test_chip_overlap_all_matches():
    """
    Test overlap calculation when all peaks match.
    """
    predicted_peaks = [
        {"chrom": "chr1", "start": 100, "end": 200, "motif": "MA0001"},
        {"chrom": "chr1", "start": 300, "end": 400, "motif": "MA0001"},
    ]
    
    chip_peaks = [
        {"chrom": "chr1", "start": 100, "end": 200},
        {"chrom": "chr1", "start": 300, "end": 400},
    ]
    
    overlap_pct = validate_motifs(predicted_peaks, chip_peaks)
    assert overlap_pct == 100.0, f"Expected 100% overlap, got {overlap_pct}%"

def test_chip_overlap_partial_threshold():
    """
    Test that peaks below the overlap threshold are not counted.
    """
    predicted_peaks = [
        {"chrom": "chr1", "start": 100, "end": 200, "motif": "MA0001"},
    ]
    
    # Chip peak overlaps by only 10bp (10/100 = 10% overlap)
    chip_peaks = [
        {"chrom": "chr1", "start": 190, "end": 200},
    ]
    
    overlap_pct = validate_motifs(predicted_peaks, chip_peaks, overlap_threshold=0.5)
    assert overlap_pct == 0.0, f"Expected 0% overlap (below threshold), got {overlap_pct}%"

def test_silhouette_score_calculation():
    """
    Test that silhouette score is calculated correctly.
    """
    # Create data with clear clusters
    data = np.array([
        [0, 0], [0.1, 0.1], [0, 0.1],  # Cluster 1
        [5, 5], [5.1, 5.1], [5, 5.1],  # Cluster 2
    ])
    
    from code.validate import calculate_silhouette_score
    silhouette_score = calculate_silhouette_score(data)
    
    # With well-separated clusters, silhouette score should be high (> 0.5)
    assert -1 <= silhouette_score <= 1, \
        f"Silhouette score {silhouette_score} should be in [-1, 1]"
    assert silhouette_score > 0.5, \
        f"Well-separated clusters should have high silhouette score, got {silhouette_score}"

def test_silhouette_score_single_cluster():
    """
    Test silhouette score for data that forms a single cluster.
    """
    data = np.array([
        [0, 0], [0.1, 0.1], [0, 0.1], [0.05, 0.05],
    ])
    
    from code.validate import calculate_silhouette_score
    silhouette_score = calculate_silhouette_score(data)
    
    # Single cluster should have lower silhouette score
    assert -1 <= silhouette_score <= 1, \
        f"Silhouette score {silhouette_score} should be in [-1, 1]"