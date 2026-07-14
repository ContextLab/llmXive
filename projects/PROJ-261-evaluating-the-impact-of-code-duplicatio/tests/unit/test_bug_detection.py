import pandas as pd
import pytest

from bug_detection import (
    load_humaneval_dataset,
    load_clone_metrics,
    compute_pass1_accuracy,
    save_results,
)
from pathlib import Path

# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------
@pytest.fixture
def dummy_clone_metrics(tmp_path):
    """Create a minimal clone‑metrics CSV for testing."""
    path = tmp_path / "clone_metrics.csv"
    df = pd.DataFrame({"clone_density": [0.42]})
    df.to_csv(path, index=False)
    # Patch the constant used in the module.
    import importlib
    bug_mod = importlib.import_module("bug_detection")
    bug_mod.CLONE_METRICS_PATH = path
    return path

# -------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------
def test_load_humaneval_dataset():
    df = load_humaneval_dataset(sample_size=5, seed=123)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5
    assert "prompt" in df.columns

def test_load_clone_metrics(dummy_clone_metrics):
    df = load_clone_metrics()
    assert isinstance(df, pd.DataFrame)
    assert "clone_density" in df.columns
    assert pd.api.types.is_float_dtype(df["clone_density"])

def test_compute_pass1_accuracy():
    # Minimal synthetic HumanEval frame – the heuristic looks for the word “return”.
    df_humaneval = pd.DataFrame(
        {
            "prompt": [
                "def foo():\\n    return 1",
                "def bar():\\n    pass",
            ]
        }
    )
    df_clone = pd.DataFrame({"clone_density": [0.5]})
    result = compute_pass1_accuracy(df_humaneval, df_clone)
    # Should return a DataFrame with the required columns.
    assert set(result.columns) == {"problem_id", "clone_density", "passed", "pass@1"}
    # Passed flag should be [1, 0] based on the heuristic.
    assert result["passed"].tolist() == [1, 0]
    # pass@1 is the cumulative mean: first row 1.0, second row 0.5
    assert result["pass@1"].tolist() == [1.0, 0.5]

def test_save_results(tmp_path):
    df = pd.DataFrame({"a": [1, 2]})
    out_path = tmp_path / "out.csv"
    save_results(df, out_path)
    assert out_path.is_file()
    reloaded = pd.read_csv(out_path)
    pd.testing.assert_frame_equal(df, reloaded)