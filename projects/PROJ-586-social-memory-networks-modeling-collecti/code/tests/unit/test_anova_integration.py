import pytest
from analysis.anova import run_anova_analysis

def test_anova_integration(tmp_path):
    # Create a small CSV file
    csv_path = tmp_path / "results_full.csv"
    csv_path.write_text(
        "game_id,context_condition,agent_count,specialization_index,retrieval_efficiency\\n"
        "1,full,5,2,0.85\\n"
        "2,limited,5,1,0.65\\n"
    )
    result = run_anova_analysis(csv_path)
    assert result is not None
