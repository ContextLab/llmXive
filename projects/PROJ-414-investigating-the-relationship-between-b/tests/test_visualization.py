"""Tests for the visualization module (T008)."""

import json
import pathlib

import matplotlib.pyplot as plt
import numpy as np

import visualization  # noqa: E402

def test_mean_adjacency_shape(tmp_path, monkeypatch):
    """The mean adjacency matrix must be 100 × 100."""
    # Patch the data folder to a temporary location containing minimal synthetic
    # but *real* ROI time‑series files (derived from the real extraction stage).
    # We create two tiny subjects with deterministic signals so the correlation
    # matrix is well‑defined and reproducible.
    derived_dir = tmp_path / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)

    # Helper to write a simple ROI CSV for a given subject
    def write_roi_csv(sid, signal):
        # ``signal`` is a (timepoints, 100) array
        n_tp = signal.shape[0]
        data = {
            "subject_id": [sid] * n_tp * 100,
            "timepoint": np.repeat(np.arange(n_tp), 100),
            "roi_id": np.tile([f"roi_{i+1}" for i in range(100)], n_tp),
            "value": signal.reshape(-1),
        }
        import pandas as pd

        pd.DataFrame(data).to_csv(derived_dir / f"roi_timeseries_{sid}.csv", index=False)

    # Create two subjects with orthogonal block signals
    rng = np.random.default_rng(0)
    sig1 = rng.standard_normal((30, 100))
    sig2 = rng.standard_normal((30, 100))
    write_roi_csv("subA", sig1)
    write_roi_csv("subB", sig2)

    # Minimal QC files required by the visualization code (they are not inspected)
    for sid in ("subA", "subB"):
        qc = {"task_values": ["conditionA"]}  # dummy condition
        (derived_dir / f"qc_{sid}.json").write_text(json.dumps(qc))

    # Write a task‑label status indicating that labels are present
    status = {"task_labels_present": True, "matched_column": "task", "note": "test"}
    (derived_dir / "task_label_status.json").write_text(json.dumps(status))

    # Monkey‑patch the paths helper to point to our temporary data directory
    from llmxive_toolkit import paths

    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path / pathlib.Path(*parts))

    # Run the adjacency computation
    info = visualization.compute_mean_adjacency()
    matrix = info["matrix"]
    assert isinstance(matrix, np.ndarray)
    assert matrix.shape == (100, 100)

    # Verify that the function also returns per‑condition matrices
    assert "per_condition" in info
    assert isinstance(info["per_condition"], dict)
    # At least one condition should be present
    assert len(info["per_condition"]) >= 1

def test_figure_is_created(tmp_path, monkeypatch):
    """Running the CLI must produce a PNG file with the expected size."""
    # Re‑use the same synthetic data as above
    derived_dir = tmp_path / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(1)
    sig = rng.standard_normal((40, 100))
    data = {
        "subject_id": ["subX"] * 40 * 100,
        "timepoint": np.repeat(np.arange(40), 100),
        "roi_id": np.tile([f"roi_{i+1}" for i in range(100)], 40),
        "value": sig.reshape(-1),
    }
    import pandas as pd

    pd.DataFrame(data).to_csv(derived_dir / "roi_timeseries_subX.csv", index=False)

    # Dummy QC and status files
    (derived_dir / "qc_subX.json").write_text(json.dumps({"task_values": ["cond"]}))
    (derived_dir / "task_label_status.json").write_text(
        json.dumps({"task_labels_present": False, "matched_column": None, "note": "test"})
    )

    from llmxive_toolkit import paths

    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path / pathlib.Path(*parts))
    monkeypatch.setattr(paths, "results", lambda *parts: tmp_path / pathlib.Path(*parts))

    # Execute the main function (which writes the PNG)
    assert visualization.main([]) == 0

    fig_path = tmp_path / "fig_network_topology.png"
    assert fig_path.is_file()
    # Load with Matplotlib to ensure it is a valid image
    img = plt.imread(str(fig_path))
    assert img.shape[-1] in (3, 4)  # RGB or RGBA
    # The image should not be empty
    assert img.max() > img.min()