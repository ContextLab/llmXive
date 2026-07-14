"""Basic sanity test for the parallelised graph‑metrics script."""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure the project root is on the path so imports work when tests are run
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from code import __main__ as compute_module  # noqa: E402


@pytest.fixture
def empty_eligible_csv(tmp_path):
    """Create an empty eligible_subjects.csv with the correct header."""
    csv_path = tmp_path / "data" / "processed" / "eligible_subjects.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=["subject_id"]).to_csv(csv_path, index=False)
    return csv_path


def test_compute_graph_metrics_runs_without_subjects(monkeypatch, tmp_path, empty_eligible_csv):
    """The script should finish without error even when there are no subjects."""
    # Patch the configuration to point to the temporary directory
    def fake_load_config():
        return {
            "n_jobs": 2,
            "output_path": tmp_path / "data" / "processed" / "graph_metrics.csv",
            "connectivity_dir": tmp_path / "data" / "processed" / "connectivity_matrices",
            "eligible_subjects_path": empty_eligible_csv,
        }

    monkeypatch.setattr(compute_module, "load_config", fake_load_config)

    # Run the main function
    exit_code = compute_module.main()
    assert exit_code == 0

    # Verify that an (empty) CSV was produced with the expected columns
    out_path = tmp_path / "data" / "processed" / "graph_metrics.csv"
    assert out_path.is_file()
    df = pd.read_csv(out_path)
    expected_cols = [
        "subject_id",
        "degree_centrality_mean",
        "global_efficiency",
        "clustering_coefficient_mean",
        "average_shortest_path_length",
    ]
    assert list(df.columns) == expected_cols
    # No rows should be present
    assert df.shape[0] == 0