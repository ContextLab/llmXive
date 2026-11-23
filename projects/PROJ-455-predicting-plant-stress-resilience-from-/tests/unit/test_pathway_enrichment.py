"""
Unit tests for pathway enrichment analysis.
"""
import pytest
import pandas as pd
from code.analysis.pathway import enrichment_analysis, validate_alignment, map_to_kegg

def test_enrichment_analysis_empty_list():
    pathways = {"Test": {"C00001"}}
    jaccard, p_value = enrichment_analysis([], pathways)
    assert jaccard == 0.0
    assert p_value == 1.0

def test_enrichment_analysis_perfect_match():
    pathways = {"Test": {"C00001", "C00002"}}
    kegg_ids = ["C00001", "C00002"]
    jaccard, p_value = enrichment_analysis(kegg_ids, pathways)
    # Jaccard = |{C00001, C00002} intersect {C00001, C00002}| / |{C00001, C00002} union {C00001, C00002}|
    # Jaccard = 2 / 2 = 1.0
    assert jaccard == 1.0
    # P-value should be very small for perfect match
    assert p_value <= 0.05

def test_enrichment_analysis_no_overlap():
    pathways = {"Test": {"C00001", "C00002"}}
    kegg_ids = ["C00003", "C00004"]
    jaccard, p_value = enrichment_analysis(kegg_ids, pathways)
    assert jaccard == 0.0
    assert p_value == 1.0

def test_validate_alignment_high_jaccard():
    assert validate_alignment(0.4, 0.1) is True
    assert validate_alignment(0.3, 0.1) is True

def test_validate_alignment_low_p_value():
    assert validate_alignment(0.1, 0.04) is True
    assert validate_alignment(0.1, 0.01) is True

def test_validate_alignment_neither():
    assert validate_alignment(0.2, 0.1) is False
    assert validate_alignment(0.29, 0.06) is False

def test_map_to_kegg():
    data = {
        "metabolite": ["Glucose", "Unknown_Metabolite", "Fructose"]
    }
    df = pd.DataFrame(data)
    result_df = map_to_kegg(df)
    assert "kegg_id" in result_df.columns
    assert result_df.loc[0, "kegg_id"] == "C00031"
    assert pd.isna(result_df.loc[1, "kegg_id"])
    assert result_df.loc[2, "kegg_id"] == "C00095"
