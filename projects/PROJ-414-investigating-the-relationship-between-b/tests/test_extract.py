"""Tests for T003 vertex-block extraction and cleaning."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from jsonschema import validate

from llmxive_toolkit import paths

CODE_DIR = paths.root / "code"
sys.path.insert(0, str(CODE_DIR))

import extract_rois  # noqa: E402
import config  # noqa: E402

SCHEMA_PATH = (paths.root / "specs" / "001-investigating-the-relationship-between-b"
                / "contracts" / "roi_timeseries.schema.yaml")


# ------------------------------------------------------------------
# Unit tests: deterministic block scheme and block means
# ------------------------------------------------------------------
def test_block_ids():
    ids = extract_rois.vertex_block_ids()
    assert len(ids) == 100
    assert ids[0] == "roi_1" and ids[-1] == "roi_100"
    assert len(set(ids)) == 100


def test_block_assignment_contiguous_deterministic():
    a = extract_rois.block_assignment(1000)
    assert a.shape == (1000,)
    assert set(np.unique(a)) == set(range(100))
    # contiguous: block index is non-decreasing
    assert np.all(np.diff(a) >= 0)
    # deterministic across calls
    assert np.array_equal(a, extract_rois.block_assignment(1000))


def test_compute_block_means():
    # 2 timepoints, 200 vertices: first 100 vertices constant 1,
    # second 100 constant 3 -> block means 1 and 3 at each timepoint.
    mat = np.zeros((2, 200))
    mat[:, :100] = 1.0
    mat[:, 100:] = 3.0
    bm = extract_rois.compute_block_means(mat)
    assert bm.shape == (2, 100)
    assert np.allclose(bm[:, 0], 1.0)
    assert np.allclose(bm[:, 99], 3.0)


# ------------------------------------------------------------------
# Unit tests: QC bad-volume rules (edge cases)
# ------------------------------------------------------------------
def _smooth_matrix(n_t=100, n_b=100):
    t = np.arange(n_t)
    base = np.sin(2 * np.pi * t / n_t)
    return base[:, None] * (1 + 0.001 * np.arange(n_b)[None, :])


def test_dvars_exclusion_fires_on_known_bad_volumes():
    """Injected spikes at 30% of volumes must trigger exclusion."""
    mat = _smooth_matrix()
    spike_volumes = list(range(10, 40))  # 30 of 100 volumes
    for v in spike_volumes:
        mat[v, :] += 50.0
    qc = extract_rois.qc_from_block_matrix(mat, fd_values=None)
    assert qc["fraction_bad_volumes"] > config.MAX_BAD_VOLUME_FRACTION
    assert qc["excluded"] is True
    assert qc["exclusion_reason"] is not None
    assert "excessive_bad_volumes" in qc["exclusion_reason"]
    assert qc["motion_proxy"]["method"] == "dvars_mad"
    assert qc["motion_proxy"]["thresholds"]["mad_multiplier"] == 3.0


def test_dvars_clean_series_not_excluded():
    qc = extract_rois.qc_from_block_matrix(_smooth_matrix(), fd_values=None)
    assert qc["excluded"] is False
    assert qc["exclusion_reason"] is None


def test_fd_rule_threshold():
    fd = np.array([0.1, 0.6, 0.5, 0.51, 0.2])
    bad = extract_rois.fd_bad_mask(fd)
    # strictly greater than 0.5 mm
    assert list(bad) == [False, True, False, True, False]


def test_fd_exclusion_path():
    mat = _smooth_matrix(n_t=10)
    fd = np.zeros(10)
    fd[:3] = 1.0  # 30% bad by FD rule
    qc = extract_rois.qc_from_block_matrix(mat, fd_values=fd)
    assert qc["excluded"] is True
    assert qc["motion_proxy"]["method"] == "fd"
    assert qc["motion_proxy"]["thresholds"]["fd_mm"] == 0.5


# ------------------------------------------------------------------
# Unit tests: bandpass filter
# ------------------------------------------------------------------
def test_bandpass_attenuates_high_frequency():
    tr = config.TR_SECONDS
    t = np.arange(600) * tr
    low = np.sin(2 * np.pi * 0.05 * t)          # in band
    high = np.sin(2 * np.pi * 0.4 * t)          # out of band
    mat = np.column_stack([low, high])
    filt, applied = extract_rois.bandpass_filter(mat)
    assert applied is True
    assert np.std(filt[:, 0]) > 0.5 * np.std(low)
    assert np.std(filt[:, 1]) < 0.2 * np.std(high)


def test_bandpass_short_run_skipped_honestly():
    mat = _smooth_matrix(n_t=10)
    filt, applied = extract_rois.bandpass_filter(mat)
    assert applied is False
    assert np.array_equal(filt, mat)


# ------------------------------------------------------------------
# Unit tests: bold orientation
# ------------------------------------------------------------------
def test_orient_frame_major():
    mat = np.arange(20, dtype=float).reshape(4, 5)  # 4 frames, 5 "vertices"
    out = extract_rois._orient_matrix(mat, 4)
    assert out.shape == (4, 5)


def test_orient_vertex_major_flat():
    # 5 vertices x 4 frames, stored vertex-major flat
    mat = np.arange(20, dtype=float).reshape(5, 4)
    flat = mat.reshape(-1)
    # pretend 4 frames; implied V=5 not a known surface count and
    # < 1000, so the honest path raises
    with pytest.raises(ValueError):
        extract_rois._orient_matrix(flat, 4)


# ------------------------------------------------------------------
# Contract test on real outputs (skipped if extraction not yet run)
# ------------------------------------------------------------------
def _derived_files():
    d = paths.data("derived")
    return sorted(d.glob("roi_timeseries_*.csv"))


def test_real_outputs_conform_to_schema():
    files = _derived_files()
    if not files:
        pytest.skip("no derived timeseries yet — run code/extract_rois.py")
    schema = yaml.safe_load(SCHEMA_PATH.read_text())
    for f in files[:3]:
        df = pd.read_csv(f)
        assert df["roi_id"].nunique() == 100
        assert set(df["roi_id"]) == set(extract_rois.vertex_block_ids())
        assert df["timepoint"].min() == 0
        for row in df.head(50).to_dict(orient="records"):
            validate(row, schema)
        sid = f.stem.replace("roi_timeseries_", "")
        qc_path = paths.data("derived", f"qc_{sid}.json")
        assert qc_path.is_file()
        qc = json.loads(qc_path.read_text())
        assert "fraction_bad_volumes" in qc
        assert "excluded" in qc
        assert "motion_proxy" in qc
        if qc["excluded"]:
            assert qc["exclusion_reason"]


def test_exclusion_log_covers_all_subjects():
    files = _derived_files()
    log_path = paths.data("derived", "exclusion_log.csv")
    if not files or not log_path.is_file():
        pytest.skip("no derived outputs yet")
    log_df = pd.read_csv(log_path)
    assert set(log_df["subject_id"]) == {
        f.stem.replace("roi_timeseries_", "") for f in files
    }
    excluded = log_df[log_df["excluded"] == True]  # noqa: E712
    assert (excluded["exclusion_reason"].str.len() > 0).all()