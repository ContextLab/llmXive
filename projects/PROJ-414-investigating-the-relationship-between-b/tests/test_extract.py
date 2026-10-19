import json
import pathlib

import pytest

import extract_rois  # noqa: E402

def test_vertex_block_ids():
    ids = extract_rois.vertex_block_ids()
    assert len(ids) == 100
    assert ids[0] == "roi_1"
    assert ids[-1] == "roi_100"

def test_block_assignment():
    assign = extract_rois.block_assignment(1000, n_blocks=100)
    # Each block should have roughly 10 vertices
    counts = [np.sum(assign == i) for i in range(100)]
    assert all(c == 10 for c in counts)

def test_compute_block_means():
    mat = np.arange(200).reshape(2, 100)  # 2 timepoints, 100 vertices
    means = extract_rois.compute_block_means(mat, n_blocks=10)
    assert means.shape == (2, 10)
    # Each block mean should be the average of 10 consecutive numbers
    expected = np.mean(mat.reshape(2, 10, 10), axis=2)
    np.testing.assert_allclose(means, expected)

def test_bandpass_filter_applied():
    # Create a short time series that will be filtered
    rng = np.random.default_rng(0)
    mat = rng.normal(size=(200, 100))
    filtered, applied = extract_rois.bandpass_filter(mat)
    assert applied is True
    assert filtered.shape == mat.shape

def test_dvars_statistics():
    # Construct a block matrix with a known bad volume
    block_mat = np.vstack([np.zeros((5, 100)), np.ones((1, 100))*10, np.zeros((5, 100))])
    dvars, bad, med, mad, thresh = extract_rois.dvars_statistics(block_mat)
    assert bad.sum() == 1
    assert np.isfinite(thresh)

def test_qc_exclusion():
    block_mat = np.random.rand(100, 100)
    qc = extract_rois.qc_from_block_matrix(block_mat)
    assert "fraction_bad_volumes" in qc
    # With random data the exclusion flag should be False most of the time
    assert qc["excluded"] in (True, False)

def test_full_extraction(tmp_path, monkeypatch):
    # Patch paths to use a temporary directory
    from llmxive_toolkit import paths
    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path / pathlib.Path(*parts))

    # Create a minimal parquet file with a single subject
    import pyarrow as pa
    import pyarrow.parquet as pq

    n_timepoints = 50
    n_vertices = 1000
    bold = np.random.rand(n_timepoints * n_vertices).astype(np.float32)
    table = pa.table({
        "sub": ["S01"],
        "n_frames": [n_timepoints],
        "bold": [bold.tolist()],  # store as list
    })
    shard_path = tmp_path / "test.parquet"
    pq.write_table(table, shard_path)

    # Write a minimal column inventory JSON
    inv = {
        "subject_column": "sub",
        "columns": ["sub", "n_frames", "bold"],
        "available_subject_count": 1,
        "expected_fields": {"fd": {"present": False}, "task_labels": {"present": False}},
    }
    (tmp_path / "column_inventory.json").write_text(json.dumps(inv))

    # Run the extraction
    extract_rois.main(["--shard", str(shard_path)])

    # Verify output files exist
    derived_dir = tmp_path / "derived"
    assert (derived_dir / "roi_timeseries_S01.csv").is_file()
    assert (derived_dir / "qc_S01.json").is_file()
    assert (derived_dir / "exclusion_log.csv").is_file()