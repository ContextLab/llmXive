import csv
import os
import math
import pytest
from code.preprocessing import calculate_distance, map_te_to_genes, identify_ambiguous_pairs

# Helper to load a small subset of mock data for deterministic testing
def load_mock_gene_models():
    # Minimal gene model with known coordinates
    return [
        {'gene_id': 'geneA', 'tss': '1000', 'tes': '2000'},
        {'gene_id': 'geneB', 'tss': '5000', 'tes': '6000'},
    ]

def load_mock_te_coordinates():
    # TE positions such that one is proximal to geneA, another ambiguous (near both)
    return [
        {'te_id': 'TE1', 'position': '1200'},   # within 5kb of geneA only
        {'te_id': 'TE2', 'position': '5500'},   # within 5kb of both geneA and geneB (ambiguous)
    ]

def test_calculate_distance():
    # Simple distance calculation
    assert calculate_distance(1500, 1000) == 500
    assert calculate_distance(8000, 2000) == 6000

def test_map_te_to_genes_proximity():
    gene_models = load_mock_gene_models()
    te_coords = load_mock_te_coordinates()
    # Use max_dist=5000 (5kb)
    pairs = map_te_to_genes(te_coords, gene_models, max_dist=5000)
    
    # Expect TE1 paired with geneA (proximal_flag=True)
    te1_pairs = [p for p in pairs if p['te_id'] == 'TE1']
    assert len(te1_pairs) == 1
    assert te1_pairs[0]['gene_id'] == 'geneA'
    assert te1_pairs[0]['proximity_flag'] is True
    assert te1_pairs[0].get('ambiguous_flag') is None
    
    # TE2 should be paired with both genes and flagged ambiguous
    te2_pairs = [p for p in pairs if p['te_id'] == 'TE2']
    assert len(te2_pairs) == 2
    gene_ids = {p['gene_id'] for p in te2_pairs}
    assert gene_ids == {'geneA', 'geneB'}
    for p in te2_pairs:
        assert p['proximity_flag'] is True
        assert p['ambiguous_flag'] is True

def test_identify_ambiguous_pairs():
    # Build a list of pairs where TE2 is ambiguous
    pairs = [
        {'te_id': 'TE1', 'gene_id': 'geneA', 'proximity_flag': True},
        {'te_id': 'TE2', 'gene_id': 'geneA', 'proximity_flag': True},
        {'te_id': 'TE2', 'gene_id': 'geneB', 'proximity_flag': True},
    ]
    flagged = identify_ambiguous_pairs(pairs)
    # TE2 pairs should now have ambiguous_flag=True
    for p in flagged:
        if p['te_id'] == 'TE2':
            assert p['ambiguous_flag'] is True
        else:
            assert 'ambiguous_flag' not in p or p['ambiguous_flag'] is False