import pytest
import pandas as pd
import numpy as np

# Import the module directly (no relative import)
import connectivity  # noqa: E402

def test_window_indices():
    n_timepoints = 100
    window_frames = 20
    step_frames = 5
    indices = list(connectivity._window_indices(n_timepoints, window_frames, step_frames))
    # The last window should start at 80 and end at 100
    assert indices[-1] == (80, 100)
    # Number of windows = floor((n - window) / step) + 1
    expected = (n_timepoints - window_frames) // step_frames + 1
    assert len(indices) == expected

def test_process_subject(tmp_path, monkeypatch):
    # Create a minimal timeseries CSV for a fake subject
    subject_id = "testsub"
    ts_path = tmp_path / f"roi_timeseries_{subject_id}.csv"
    n_timepoints = 50
    n_blocks = 100
    data = {
        "subject_id": [subject_id] * n_timepoints * n_blocks,
        "timepoint": np.repeat(np.arange(n_timepoints), n_blocks),
        "roi_id": np.tile([f"roi_{i+1}" for i in range(n_blocks)], n_timepoints),
        "value": np.random.rand(n_timepoints * n_blocks),
    }
    pd.DataFrame(data).to_csv(ts_path, index=False)

    # Patch paths.data to point to our temporary directory
    from llmxive_toolkit import paths
    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path / Path(*parts))

    # Run the processing function
    connectivity._process_subject(subject_id, window_seconds=45.0, step_seconds=10.0)

    out_path = tmp_path / f"metrics_{subject_id}.csv"
    assert out_path.is_file()
    out_df = pd.read_csv(out_path)
    # Expect at least one window row
    assert len(out_df) > 0
    assert set(out_df.columns) == {
        "subject_id",
        "window_index",
        "global_efficiency",
        "modularity",
        "participation_coefficient",
    }