import pytest
import json
from code.data_models.enrichment_result import EnrichmentResult

def test_enrichment_result_creation():
    """Test basic creation of EnrichmentResult."""
    result = EnrichmentResult(
        lineage="Human",
        odds_ratio=2.5,
        p_raw=0.001,
        p_corrected_phylo=0.005,
        p_fdr=0.01,
        p_empirical=0.002
    )
    assert result.lineage == "Human"
    assert result.odds_ratio == 2.5
    assert result.p_raw == 0.001
    assert result.p_corrected_phylo == 0.005
    assert result.p_fdr == 0.01
    assert result.p_empirical == 0.002

def test_enrichment_result_to_dict():
    """Test conversion to dictionary."""
    result = EnrichmentResult(
        lineage="PanTro6",
        odds_ratio=1.8,
        p_raw=0.04,
        p_corrected_phylo=0.06,
        p_fdr=0.08,
        p_empirical=0.05
    )
    data = result.to_dict()
    assert isinstance(data, dict)
    assert data['lineage'] == "PanTro6"
    assert data['odds_ratio'] == 1.8
    assert data['p_raw'] == 0.04

def test_enrichment_result_to_json():
    """Test conversion to JSON string."""
    result = EnrichmentResult(
        lineage="RheMac10",
        odds_ratio=1.2,
        p_raw=0.15,
        p_corrected_phylo=0.20,
        p_fdr=0.25,
        p_empirical=0.18
    )
    json_str = result.to_json()
    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert data['lineage'] == "RheMac10"
    assert data['odds_ratio'] == 1.2

def test_enrichment_result_from_dict():
    """Test creation from dictionary."""
    data = {
        'lineage': "CalJac4",
        'odds_ratio': 3.1,
        'p_raw': 0.0005,
        'p_corrected_phylo': 0.002,
        'p_fdr': 0.003,
        'p_empirical': 0.001
    }
    result = EnrichmentResult.from_dict(data)
    assert result.lineage == "CalJac4"
    assert result.odds_ratio == 3.1
    assert result.p_raw == 0.0005

def test_enrichment_result_from_json():
    """Test creation from JSON string."""
    json_str = json.dumps({
        'lineage': "Human",
        'odds_ratio': 4.0,
        'p_raw': 0.0001,
        'p_corrected_phylo': 0.0004,
        'p_fdr': 0.0006,
        'p_empirical': 0.0002
    })
    result = EnrichmentResult.from_json(json_str)
    assert result.lineage == "Human"
    assert result.odds_ratio == 4.0

def test_enrichment_result_invalid_lineage():
    """Test validation of empty lineage."""
    with pytest.raises(ValueError):
        EnrichmentResult(
            lineage="",
            odds_ratio=1.0,
            p_raw=0.05,
            p_corrected_phylo=0.1,
            p_fdr=0.1,
            p_empirical=0.1
        )

def test_enrichment_result_invalid_p_value():
    """Test validation of p-values outside [0, 1]."""
    with pytest.raises(ValueError):
        EnrichmentResult(
            lineage="Human",
            odds_ratio=1.0,
            p_raw=1.5,  # Invalid
            p_corrected_phylo=0.1,
            p_fdr=0.1,
            p_empirical=0.1
        )

def test_enrichment_result_negative_odds_ratio():
    """Test validation of negative odds ratio."""
    with pytest.raises(ValueError):
        EnrichmentResult(
            lineage="Human",
            odds_ratio=-1.0,  # Invalid
            p_raw=0.05,
            p_corrected_phylo=0.1,
            p_fdr=0.1,
            p_empirical=0.1
        )

def test_enrichment_result_round_trip():
    """Test round-trip conversion."""
    original = EnrichmentResult(
        lineage="TestLineage",
        odds_ratio=2.22,
        p_raw=0.033,
        p_corrected_phylo=0.044,
        p_fdr=0.055,
        p_empirical=0.066
    )
    json_str = original.to_json()
    restored = EnrichmentResult.from_json(json_str)
    assert original.lineage == restored.lineage
    assert original.odds_ratio == restored.odds_ratio
    assert original.p_raw == restored.p_raw
    assert original.p_corrected_phylo == restored.p_corrected_phylo
    assert original.p_fdr == restored.p_fdr
    assert original.p_empirical == restored.p_empirical