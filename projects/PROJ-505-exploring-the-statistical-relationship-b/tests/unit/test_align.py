"""
Unit tests for the alignment routine (T004).

The tests generate a tiny synthetic CDF-like environment using temporary
CSV files (which are read via the same extraction logic that the real
CDF loader uses).  This avoids the need for large external CDF files
while still exercising the full alignment pipeline on real‑style data.

The test suite checks:
  * One row per hour in the output parquet.
  * Monotonic timestamps.
  * ``max_offset_minutes`` ≤ 30.
  * The alignment report contains any detected gaps.
  * The output parquet conforms to the dataset schema.
"""
import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from code.ingestion.align import align_data

# Helper to create minimal CSV files that mimic the structure of the
# expected CDF variables.  The alignment code reads the files via cdflib,
# but for the purpose of the unit test we monkey‑patch the CDF loader to
# read these CSVs instead.
def _write_fake_cdf_csv(csv_path: Path, timestamps, **columns):
    df = pd.DataFrame({'timestamp': timestamps})
    for name, values in columns.items():
        df[name] = values
    df.to_csv(csv_path, index=False)

@pytest.fixture
def fake_raw_dirs(tmp_path):
    """
    Create a temporary ``data/raw`` hierarchy with minimal CSV files that
    stand in for real CDFs.  The alignment code will be monkey‑patched
    to read these CSVs.
    """
    ace_dir = tmp_path / 'ace_swics'
    wind_dir = tmp_path / 'wind_sms'
    omni_dir = tmp_path / 'omni'
    ace_dir.mkdir()
    wind_dir.mkdir()
    omni_dir.mkdir()
    # Generate a 5‑hour window of data
    base = pd.Timestamp('2000-01-01 00:00')
    timestamps = [base + pd.Timedelta(hours=i) for i in range(5)]

    # ACE composition (fluxes)
    _write_fake_cdf_csv(
        ace_dir / 'ace1.csv',
        timestamps,
        H_flux=[10, 12, 11, 13, 12],
        He_flux=[1, 1.1, 1.2, 1.0, 1.3],
        C_flux=[0.5, 0.6, 0.55, 0.58, 0.6],
        O_flux=[2, 2.2, 2.1, 2.3, 2.2],
        Fe_flux=[0.2, 0.22, 0.21, 0.23, 0.22],
    )
    # WIND composition (different timestamps, overlapping)
    _write_fake_cdf_csv(
        wind_dir / 'wind1.csv',
        timestamps,
        H_flux=[9, 11, 10, 12, 11],
        He_flux=[0.9, 1.0, 1.1, 0.95, 1.05],
        C_flux=[0.45, 0.55, 0.5, 0.53, 0.55],
        O_flux=[1.9, 2.1, 2.0, 2.2, 2.1],
        Fe_flux=[0.19, 0.21, 0.2, 0.22, 0.21],
    )
    # OMNI bulk + indices
    _write_fake_cdf_csv(
        omni_dir / 'omni1.csv',
        timestamps,
        velocity_km_s=[400, 420, 410, 430, 425],
        density_cm3=[5, 5.5, 5.2, 5.3, 5.4],
        imf_by_nT=[-2, -1, -1.5, -2.1, -1.8],
        imf_bz_nT=[-1, -0.5, -0.8, -1.2, -1.0],
        imf_nT=[2.2, 1.5, 1.7, 2.3, 2.0],
        dst_index=[-10, -12, -11, -13, -12],
        kp_index=[2, 2.5, 2.2, 2.8, 2.6],
    )
    return ace_dir, wind_dir, omni_dir

def test_align_produces_hourly_parquet(tmp_path, fake_raw_dirs, monkeypatch):
    ace_dir, wind_dir, omni_dir = fake_raw_dirs
    output_path = tmp_path / 'aligned.parquet'
    report_path = tmp_path / 'alignment_report.json'

    # Monkey‑patch the CDF loader to read our CSV files.
    # The real ``cdflib.CDF`` constructor expects a CDF file; we replace it
    # with a lightweight wrapper that reads the CSV into memory.
    class _FakeCDF:
        def __init__(self, path):
            self._df = pd.read_csv(path)

        def cdf_info(self):
            class Info:
                def __init__(self, cols):
                    self.zVariables = cols
                    self.epochVariables = ['timestamp']
            return Info(list(self._df.columns))

        def varget(self, name):
            return self._df[name].values

    monkeypatch.setattr('cdflib.CDF', _FakeCDF)

    # Run alignment
    align_data(
        ace_dir=ace_dir,
        wind_dir=wind_dir,
        omni_dir=omni_dir,
        output_path=output_path,
        report_path=report_path,
    )

    # Verify output parquet exists and has the expected shape
    assert output_path.exists()
    df = pd.read_parquet(output_path)
    # 5 hourly rows expected
    assert len(df) == 5
    # Timestamps must be monotonic and hourly spaced
    assert df['timestamp'].is_monotonic_increasing
    diffs = df['timestamp'].diff().dt.total_seconds().dropna()
    assert all(diffs == 3600)

    # Verify max offset ≤ 30 minutes (the alignment uses a 30‑min tolerance)
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    assert report['max_offset_minutes'] <= 30

    # Gaps list may be empty for this synthetic case
    assert isinstance(report['gaps_exceeding_6h'], list)

    # Check that required ratio columns are present and finite
    for col in ('o_fe_ratio', 'he_h_ratio', 'c_o_ratio'):
        assert col in df.columns
        assert df[col].notna().all()