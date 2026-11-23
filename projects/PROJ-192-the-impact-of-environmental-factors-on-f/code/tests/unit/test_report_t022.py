import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from src.pipelines.report import (
    generate_permanova_summary,
    generate_db_rda_variance,
    run_report_pipeline_with_null_handling,
    apply_fdr_correction
)

def test_generate_permanova_summary_creates_output():
    """Test that generate_permanova_summary creates the output file and applies FDR."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        # Create dummy input without FDR
        df = pd.DataFrame({
            'term': ['pH', 'Nutrients', 'Moisture'],
            'R2': [0.15, 0.10, 0.05],
            'p-value': [0.01, 0.04, 0.06]
        })
        df.to_csv(input_path, index=False)
        
        result_df = generate_permanova_summary(str(input_path), str(output_path))
        
        assert output_path.exists()
        assert 'p-value_adj' in result_df.columns
        assert len(result_df) == 3
        # Check that p-value_adj is not NaN
        assert not result_df['p-value_adj'].isna().any()

def test_generate_db_rda_variance_creates_output():
    """Test that generate_db_rda_variance creates the output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "varpart.csv"
        output_path = Path(tmpdir) / "db_rda.csv"
        
        df = pd.DataFrame({
            'term': ['pH', 'Temp'],
            'R2': [0.20, 0.12],
            'p-value': [0.001, 0.02]
        })
        df.to_csv(input_path, index=False)
        
        result_df = generate_db_rda_variance(input_path=str(input_path), output_path=str(output_path))
        
        assert output_path.exists()
        assert 'p-value_adj' in result_df.columns
        assert len(result_df) == 2

def test_run_report_pipeline_with_null_handling():
    """Test the full T022 pipeline orchestration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create input files
        permanova_input = Path(tmpdir) / "permanova_raw.csv"
        varpart_input = Path(tmpdir) / "varpart.csv"
        
        permanova_df = pd.DataFrame({
            'term': ['pH'],
            'R2': [0.15],
            'p-value': [0.01]
        })
        permanova_df.to_csv(permanova_input, index=False)
        
        varpart_df = pd.DataFrame({
            'term': ['pH'],
            'R2': [0.15],
            'p-value': [0.01]
        })
        varpart_df.to_csv(varpart_input, index=False)
        
        out_perm = Path(tmpdir) / "permanova_summary.csv"
        out_var = Path(tmpdir) / "db_rda_variance.csv"
        
        results = run_report_pipeline_with_null_handling(
            permanova_path=str(permanova_input),
            varpart_path=str(varpart_input),
            output_permanova=str(out_perm),
            output_varpart=str(out_var)
        )
        
        assert out_perm.exists()
        assert out_var.exists()
        assert 'permanova_summary' in results
        assert 'db_rda_variance' in results

def test_apply_fdr_correction():
    """Test FDR correction logic."""
    df = pd.DataFrame({
        'term': ['A', 'B', 'C'],
        'p-value': [0.01, 0.05, 0.10]
    })
    
    result = apply_fdr_correction(df)
    
    assert 'p-value_adj' in result.columns
    # BH correction should result in values <= 1.0
    assert (result['p-value_adj'] <= 1.0).all()
    assert len(result) == 3