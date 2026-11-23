import pathlib
import pandas as pd
from llmxive_toolkit import paths

def test_complexity_artifacts_exist():
    """Verify that T007 produced the required files with correct schemas."""
    csv_path = paths.data("processed", "task_complexity.csv")
    corr_path = paths.data("processed", "correlation.txt")

    assert csv_path.exists(), "Task complexity CSV missing"
    assert corr_path.exists(), "Correlation text file missing"

    # Check CSV structure
    df = pd.read_csv(csv_path)
    assert set(df.columns) == {"clip_id", "subgoal_count"}, "CSV columns mismatch"
    assert not df.empty, "Complexity CSV is empty"
    assert df["subgoal_count"].between(1, 10).all(), "Subgoal counts must be in [1, 10]"

    # Check correlation file content
    content = corr_path.read_text()
    assert "r =" in content, "Correlation file missing 'r =' line"
    assert "p =" in content, "Correlation file missing 'p =' line"