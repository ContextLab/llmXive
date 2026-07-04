import pytest
import sys
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.results import StatisticalModel, AnalysisResult, extract_model_results, save_analysis_results

def test_statistical_model_flag():
    """
    T029 Test: Verify that StatisticalModel has is_associational flag set to True by default.
    """
    model = StatisticalModel(
        subfield="CA3",
        formula="CA3 ~ ACE_score + Age",
        beta_ace=0.5,
        se_ace=0.1,
        ci_lower=0.3,
        ci_upper=0.7,
        p_value=0.001,
        corrected_p_value=0.003,
        n_obs=1000
    )
    assert model.is_associational is True, "FR-010: Model must be flagged as associational"

def test_analysis_result_disclaimer():
    """
    T029 Test: Verify that AnalysisResult contains the associational disclaimer.
    """
    result = AnalysisResult()
    assert "ASSOCIATIONAL" in result.disclaimer, "FR-010: Disclaimer must explicitly state associational nature"
    assert "causal" not in result.disclaimer.lower() or "cannot be inferred" in result.disclaimer.lower()

def test_save_results_includes_disclaimer(tmp_path):
    """
    T029 Test: Verify that saved JSON/CSV includes the associational framing.
    """
    from code.analysis.results import StatisticalModel, AnalysisResult, save_analysis_results
    import pandas as pd

    # Create a mock result
    models = [
        StatisticalModel(
            subfield="CA3",
            formula="CA3 ~ ACE_score",
            beta_ace=0.5,
            se_ace=0.1,
            ci_lower=0.3,
            ci_upper=0.7,
            p_value=0.01,
            corrected_p_value=0.03,
            n_obs=500,
            is_associational=True
        )
    ]
    analysis = AnalysisResult(models=models)
    
    output_path = tmp_path / "model_results.json"
    save_analysis_results(analysis, output_path)
    
    # Verify JSON content
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert "disclaimer" in data, "FR-010: JSON must contain disclaimer"
    assert "ASSOCIATIONAL" in data["disclaimer"], "FR-010: JSON disclaimer must be explicit"
    assert data["models"][0]["is_associational"] is True, "FR-010: Model entry must be flagged"
    
    # Verify CSV content
    csv_path = tmp_path / "model_results.csv"
    assert csv_path.exists(), "FR-010: CSV must be generated"
    df = pd.read_csv(csv_path)
    assert "is_associational" in df.columns, "FR-010: CSV must have is_associational column"
    assert df["is_associational"].all(), "FR-010: All CSV rows must be flagged associational"
    assert "disclaimer" in df.columns, "FR-010: CSV must have disclaimer column"