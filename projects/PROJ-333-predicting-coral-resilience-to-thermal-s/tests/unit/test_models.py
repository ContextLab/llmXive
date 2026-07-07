"""
Unit tests for the data model schemas.
"""
import pytest
import pandas as pd
import numpy as np
from code.models.expression import ExpressionMatrix
from code.models.phenotype import PhenotypeRecord, TreatmentType
from code.models.dge import DGEResult

def test_expression_matrix_initialization():
    """Test basic initialization of ExpressionMatrix."""
    data = pd.DataFrame(
        [[10, 20], [30, 40]],
        index=["GeneA", "GeneB"],
        columns=["Sample1", "Sample2"]
    )
    matrix = ExpressionMatrix(counts=data)
    assert len(matrix.gene_ids) == 2
    assert len(matrix.sample_ids) == 2
    assert matrix.is_normalized is False

def test_expression_matrix_filtering():
    """Test gene filtering logic."""
    data = pd.DataFrame(
        [[10, 20], [5, 5], [100, 100]],
        index=["GeneA", "GeneB", "GeneC"],
        columns=["Sample1", "Sample2"]
    )
    matrix = ExpressionMatrix(counts=data)
    # Filter: count >= 10 in at least 1 sample
    filtered = matrix.filter_genes(min_count=10, min_samples=1)
    assert "GeneB" not in filtered.gene_ids
    assert "GeneA" in filtered.gene_ids
    assert "GeneC" in filtered.gene_ids

def test_phenotype_record_treatment_parsing():
    """Test that string treatments are parsed to Enum."""
    record = PhenotypeRecord(sample_id="S1", treatment="Heat Stress")
    assert record.treatment == TreatmentType.HEAT_STRESS

def test_phenotype_record_validation():
    """Test validation of phenotype records."""
    valid = PhenotypeRecord(sample_id="S1", treatment="Control")
    assert valid.is_valid_for_analysis is True

    invalid = PhenotypeRecord(sample_id="S1", treatment="Unknown Condition")
    assert invalid.treatment == TreatmentType.UNKNOWN
    assert invalid.is_valid_for_analysis is False

def test_dge_result_significance():
    """Test significance determination."""
    sig = DGEResult(gene_id="G1", log2_fold_change=2.0, base_mean=100, p_value=0.01, p_adjust=0.04)
    assert sig.is_significant is True

    non_sig = DGEResult(gene_id="G2", log2_fold_change=0.1, base_mean=100, p_value=0.5, p_adjust=0.8)
    assert non_sig.is_significant is False

def test_dge_result_direction():
    """Test direction calculation."""
    up = DGEResult(gene_id="G1", log2_fold_change=2.0, base_mean=100, p_value=0.01, p_adjust=0.04)
    assert up.direction == "up"

    down = DGEResult(gene_id="G2", log2_fold_change=-2.0, base_mean=100, p_value=0.01, p_adjust=0.04)
    assert down.direction == "down"

    neutral = DGEResult(gene_id="G3", log2_fold_change=0.1, base_mean=100, p_value=0.01, p_adjust=0.04)
    assert neutral.direction == "neutral"
