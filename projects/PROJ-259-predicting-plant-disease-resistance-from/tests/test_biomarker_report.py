import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.biomarker_report import (
    load_selection_frequency,
    load_effect_sizes,
    calculate_aggregated_metrics,
    apply_significance_filter,
    rank_and_sort,
    generate_biomarker_report
)
from config import get_artifacts_path

@pytest.fixture
def mock_artifacts_dir(tmp_path):
    """Create a temporary artifacts directory structure."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    
    # Mock selection_frequency.csv
    freq_data = {
        'feature_id': ['SNP_001', 'SNP_002', 'MET_001', 'MET_002'],
        'threshold': [0.01, 0.01, 0.01, 0.01],
        'frequency': [0.9, 0.4, 0.8, 0.2]
    }
    freq_df = pd.DataFrame(freq_data)
    freq_df.to_csv(reports_dir / "selection_frequency.csv", index=False)
    
    # Mock effect_sizes.csv
    eff_data = {
        'feature_id': ['SNP_001', 'SNP_002', 'MET_001', 'MET_002'],
        'effect_size': [1.5, -0.2, 2.1, -0.1],
        'p_value': [0.001, 0.3, 0.0005, 0.4]
    }
    eff_df = pd.DataFrame(eff_data)
    eff_df.to_csv(reports_dir / "effect_sizes.csv", index=False)
    
    return tmp_path

def test_load_selection_frequency(mock_artifacts_dir):
    with patch('analysis.biomarker_report.get_artifacts_path', return_value=mock_artifacts_dir):
        df = load_selection_frequency()
        assert len(df) == 4
        assert 'frequency' in df.columns
        assert df['frequency'].dtype in [np.float64, np.int64]

def test_load_effect_sizes(mock_artifacts_dir):
    with patch('analysis.biomarker_report.get_artifacts_path', return_value=mock_artifacts_dir):
        df = load_effect_sizes()
        assert len(df) == 4
        assert 'effect_size' in df.columns

def test_calculate_aggregated_metrics(mock_artifacts_dir):
    with patch('analysis.biomarker_report.get_artifacts_path', return_value=mock_artifacts_dir):
        freq_df = load_selection_frequency()
        eff_df = load_effect_sizes()
        agg = calculate_aggregated_metrics(freq_df, eff_df)
        
        assert len(agg) == 4 # Unique features
        assert 'frequency' in agg.columns
        assert 'effect_size' in agg.columns
        assert 'p_value' in agg.columns

def test_apply_significance_filter(mock_artifacts_dir):
    with patch('analysis.biomarker_report.get_artifacts_path', return_value=mock_artifacts_dir):
        freq_df = load_selection_frequency()
        eff_df = load_effect_sizes()
        agg = calculate_aggregated_metrics(freq_df, eff_df)
        
        # Filter with strict thresholds
        filtered = apply_significance_filter(agg, p_threshold=0.05, freq_threshold=0.5)
        
        # SNP_001 (freq 0.9, p 0.001) should pass
        # MET_001 (freq 0.8, p 0.0005) should pass
        # SNP_002 (freq 0.4) should fail freq
        # MET_002 (freq 0.2) should fail freq
        assert len(filtered) == 2
        assert 'SNP_001' in filtered['feature_id'].values
        assert 'MET_001' in filtered['feature_id'].values

def test_rank_and_sort(mock_artifacts_dir):
    with patch('analysis.biomarker_report.get_artifacts_path', return_value=mock_artifacts_dir):
        freq_df = load_selection_frequency()
        eff_df = load_effect_sizes()
        agg = calculate_aggregated_metrics(freq_df, eff_df)
        filtered = apply_significance_filter(agg, p_threshold=0.05, freq_threshold=0.5)
        
        ranked = rank_and_sort(filtered)
        
        # SNP_001 (freq 0.9) should be rank 1
        # MET_001 (freq 0.8) should be rank 2
        assert ranked.iloc[0]['feature_id'] == 'SNP_001'
        assert ranked.iloc[0]['rank'] == 1
        assert ranked.iloc[1]['feature_id'] == 'MET_001'
        assert ranked.iloc[1]['rank'] == 2

def test_generate_biomarker_report(mock_artifacts_dir):
    with patch('analysis.biomarker_report.get_artifacts_path', return_value=mock_artifacts_dir):
        output_path = generate_biomarker_report(p_threshold=0.05, freq_threshold=0.5)
        
        assert os.path.exists(output_path)
        assert output_path.endswith("top_features.csv")
        
        report_df = pd.read_csv(output_path)
        assert 'rank' in report_df.columns
        assert 'feature_id' in report_df.columns
        assert 'p_adjusted' in report_df.columns
        assert len(report_df) == 2
        assert report_df.iloc[0]['feature_id'] == 'SNP_001'