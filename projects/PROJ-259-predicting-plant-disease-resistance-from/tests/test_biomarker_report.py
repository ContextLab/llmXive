import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from analysis.biomarker_report import (
    load_feature_selection_results,
    load_effect_sizes,
    apply_significance_filter,
    generate_biomarker_report
)
from utils.exceptions import PipelineException

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def mock_selection_freq(temp_dir):
    data = {
        "feature_id": ["SNP_1", "SNP_2", "MET_1", "MET_2"],
        "threshold": [0.01, 0.01, 0.01, 0.01],
        "frequency": [0.9, 0.5, 0.8, 0.3]
    }
    path = temp_dir / "selection_frequency.csv"
    pd.DataFrame(data).to_csv(path, index=False)
    return path

@pytest.fixture
def mock_effect_sizes(temp_dir):
    data = {
        "feature_id": ["SNP_1", "SNP_2", "MET_1", "MET_2"],
        "effect_size": [0.5, 0.2, -0.4, 0.1],
        "p_value": [0.01, 0.2, 0.03, 0.6],
        "feature_type": ["snp", "snp", "metabolite", "metabolite"]
    }
    path = temp_dir / "effect_sizes.csv"
    pd.DataFrame(data).to_csv(path, index=False)
    return path

def test_load_feature_selection_results(mock_selection_freq):
    df = load_feature_selection_results(mock_selection_freq)
    assert "feature_id" in df.columns
    assert "frequency" in df.columns
    assert len(df) == 4

def test_load_effect_sizes(mock_effect_sizes):
    df = load_effect_sizes(mock_effect_sizes)
    assert "effect_size" in df.columns
    assert "p_value" in df.columns
    assert len(df) == 4

def test_load_missing_file(temp_dir):
    with pytest.raises(PipelineException) as exc_info:
        load_feature_selection_results(temp_dir / "nonexistent.csv")
    assert "FILE_NOT_FOUND" in str(exc_info.value.code)

def test_apply_significance_filter(mock_selection_freq, mock_effect_sizes):
    # Load and merge manually for test
    freq_df = load_feature_selection_results(mock_selection_freq)
    effect_df = load_effect_sizes(mock_effect_sizes)
    
    freq_agg = freq_df.groupby('feature_id').agg({'frequency': 'mean'}).reset_index()
    merged = pd.merge(effect_df, freq_agg, on='feature_id', how='inner')
    
    # Filter: p < 0.05 and freq > 0.6
    filtered = apply_significance_filter(merged, p_value_threshold=0.05, min_frequency=0.6)
    
    # SNP_1: p=0.01, freq=0.9 -> Keep
    # MET_1: p=0.03, freq=0.8 -> Keep
    # SNP_2: p=0.2 -> Drop
    # MET_2: p=0.6 -> Drop
    
    assert len(filtered) == 2
    assert "SNP_1" in filtered["feature_id"].values
    assert "MET_1" in filtered["feature_id"].values

def test_generate_biomarker_report(mock_selection_freq, mock_effect_sizes, temp_dir):
    output_path = temp_dir / "top_features.csv"
    
    stats = generate_biomarker_report(
        selection_frequency_path=mock_selection_freq,
        effect_sizes_path=mock_effect_sizes,
        output_path=output_path,
        p_value_threshold=0.05,
        min_frequency=0.6
    )
    
    assert output_path.exists()
    assert stats["significant_features_count"] == 2
    assert stats["snps_count"] == 1
    assert stats["metabolites_count"] == 1
    
    result_df = pd.read_csv(output_path)
    assert "SNP_1" in result_df["feature_id"].values
    assert "MET_1" in result_df["feature_id"].values