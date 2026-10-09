"""
Data ingestion module for OpenNeuro MEG dataset ds000246.

Primary path (per tasks.md): stream via Hugging Face ``datasets`` with
``load_dataset("openneuro/ds000246", split="train", streaming=True)``.

The previous run of this script failed because that Hub repository does
not exist (DatasetNotFoundError). The script therefore falls back to the
canonical, programmatically-accessible OpenNeuro S3 bucket
(https://openneuro.org.s3.amazonaws.com/ds000246/...), which hosts the
real, published raw MEG recordings of ds000246 (Elekta Neuromag .fif
files). This is a REAL data source, not a synthetic stand-in.

The fallback streams:
  1. the S3 object listing (paginated),
  2. the smallest suitable raw MEG file (chunked HTTP download),
  3. the sensor time-series out of the .fif via mne in chunks,
and appends each chunk to a Parquet writer, so the full raw file is
never held in RAM. Under the runner's RAM/compute budget a well-defined
real subsample is stored (first MAX_CHANNELS channels, first
MAX_SAMPLES time points); the exact subsampling parameters are recorded
in the Parquet schema metadata so the limitation is transparent.

Any failure of BOTH real fetch paths raises (no synthetic fallback).
"""

import json
import sys
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

DATASET_ID = "ds000246"
S3_BASE = "https://openneuro.org.s3.amazonaws.com/"
S3_NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"

# Subsampling caps (documented resource limitation, see spec edge case
# "Resource exhaustion"). These define a well-defined REAL sample of the
# full recording, not a synthetic stand-in.
MAX_CHANNELS = 64
MAX_SAMPLES = 60000
CHUNK_SAMPLES = 2000
PREFERRED_FILE_CAP_BYTES = 250 * 1024 * 1024
ABSOLUTE_FILE_CAP_BYTES = 400 * 1024 * 1024


def _try_huggingface_stream(output_path: str) -> int:
    """Stream the dataset via Hugging Face ``datasets`` (primary path).

    Returns the number of rows written. Raises on any fetch error.
    """
    from datasets import load_dataset  # imported lazily

    print("Attempting primary path: Hugging Face datasets streaming...")
    dataset = load_dataset(
        "openneuro/ds000246", split="train", streaming=True
    )
    writer = None
    row_count = 0
    for batch in dataset:
        df_batch = pd.DataFrame([batch])
        if df_batch.empty:
            continue
        table = pa.Table.from_pandas(df_batch, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(output_path, table.schema)
        writer.write_table(table)
        row_count += len(df_batch)
    if writer is None or row_count == 0:
        raise RuntimeError(
            "Hugging Face stream for openneuro/ds000246 returned no rows."
        )
    writer.close()
    return row_count


def list_s3_objects(prefix: str):
    """List (key, size) pairs for all objects under ``prefix``."""
    keys = []
    token = None
    while True:
        params = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            params["continuation-token"] = token
        url = S3_BASE + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=60) as resp:
            tree = ET.fromstring(resp.read())
        for content in tree.findall(S3_NS + "Contents"):
            keys.append(
                (content.findtext(S3_NS + "Key"),
                 int(content.findtext(S3_NS + "Size")))
            )
        truncated = tree.findtext(S3_NS + "IsTruncated") == "true"
        token = tree.findtext(S3_NS + "NextContinuationToken")
        if not truncated:
            break
    return keys


def download_file_streaming(url: str, dest: Path, max_bytes: int) -> int:
    """Stream ``url`` to ``dest`` in 1 MiB chunks; raise if > max_bytes."""
    total = 0
    with urllib.request.urlopen(url, timeout=180) as resp, open(dest, "wb") as f:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise IOError(
                    f"Remote file exceeds download cap of {max_bytes} bytes."
                )
            f.write(chunk)
    return total


def _pick_meg_file(objects):
    """Choose the best raw MEG file from the S3 listing."""
    fifs = [
        (k, s) for (k, s) in objects
        if k.endswith(".fif") and not k.endswith(".json")
    ]
    if not fifs:
        raise RuntimeError(
            "No .fif MEG files found in OpenNeuro ds000246 S3 listing."
        )
    preferred = [
        (k, s) for (k, s) in fifs
        if ("raw" in k.lower() or "_meg" in k.lower())
        and s <= PREFERRED_FILE_CAP_BYTES and s > 0
    ]
    if preferred:
        return min(preferred, key=lambda t: t[1])
    under_cap = [(k, s) for (k, s) in fifs if 0 < s <= ABSOLUTE_FILE_CAP_BYTES]
    if under_cap:
        return min(under_cap, key=lambda t: t[1])
    # Fall back to the single smallest .fif regardless of cap.
    nonzero = [(k, s) for (k, s) in fifs if s > 0]
    if not nonzero:
        raise RuntimeError("All .fif files in ds000246 listing are empty.")
    return min(nonzero, key=lambda t: t[1])


def _stream_openneuro_s3(output_path: str) -> int:
    """Fetch a real ds000246 MEG recording from OpenNeuro S3 and write
    the sensor time-series to a Parquet file in chunks."""
    import mne

    mne.set_log_level("ERROR")

    print("Primary path unavailable; falling back to OpenNeuro S3 "
          "(real published raw MEG data)...")
    objects = list_s3_objects(f"{DATASET_ID}/")
    if not objects:
        raise RuntimeError(
          f"S3 listing for {DATASET_ID} returned no objects."
        )
    key, size = _pick_meg_file(objects)
    url = S3_BASE + urllib.parse.quote(key)
    print(f"Selected real MEG file: {key} ({size / 1e6:.1f} MB)")

    tmp_dir = Path(output_path).parent
    tmp_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(suffix=".fif", dir=str(tmp_dir))
    Path(fd).close()
    tmp_path = Path(tmp_path)
    try:
        downloaded = download_file_streaming(
            url, tmp_path, ABSOLUTE_FILE_CAP_BYTES + (1 << 20)
        )
        print(f"Downloaded {downloaded / 1e6:.1f} MB of real MEG data.")

        raw = mne.io.read_raw(str(tmp_path), preload=False, verbose="ERROR")
        sfreq = float(raw.info["sfreq"])
        n_channels_total = len(raw.ch_names)
        n_times_total = int(raw.n_times)

        n_channels = min(MAX_CHANNELS, n_channels_total)
        picks = list(range(n_channels))
        n_samples = min(MAX_SAMPLES, n_times_total)

        print(
            f"Recording: {n_channels_total} channels @ {sfreq} Hz, "
            f"{n_times_total} samples. Streaming subsample of "
            f"{n_channels} channels x {n_samples} samples to Parquet."
        )

        meta = {
            "source_dataset": "openneuro/" + DATASET_ID,
            "source_file": key,
            "source_url": url,
            "sfreq_hz": repr(sfreq),
            "n_channels_total": str(n_channels_total),
            "n_times_total": str(n_times_total),
            "n_channels_written": str(n_channels),
            "n_samples_written": str(n_samples),
            "subsample_note": (
                "first %d channels and first %d samples of the real "
                "recording (resource-limited subsample)" % (n_channels, n_samples)
            ),
        }

        writer = None
        rows_written = 0
        for start in range(0, n_samples, CHUNK_SAMPLES):
            stop = min(start + CHUNK_SAMPLES, n_samples)
            data = raw.get_data(start=start, stop=stop, picks=picks)
            df = pd.DataFrame(
                data.T, columns=[f"ch_{i:03d}" for i in range(n_channels)]
            )
            df.insert(0, "time_s", np.arange(start, stop) / sfreq)
            table = pa.Table.from_pandas(df, preserve_index=False)
            table = table.replace_schema_metadata(
                {k.encode(): v.encode() for k, v in meta.items()}
            )
            if writer is None:
                writer = pq.ParquetWriter(output_path, table.schema)
            writer.write_table(table)
            rows_written += stop - start

        if writer is None or rows_written == 0:
            raise RuntimeError("No sensor samples extracted from MEG file.")
        writer.close()
        return rows_written
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def download_meg_streamed(output_path: str = "data/raw/meg_streamed.parquet") -> None:
    """
    Download real OpenNeuro ds000246 MEG data and save to Parquet.

    Tries the Hugging Face streaming path first (as specified in
    tasks.md); if that repository is unavailable, streams the real raw
    MEG recording from the canonical OpenNeuro S3 bucket. Raises
    RuntimeError if no real data could be fetched (no synthetic
    fallback).
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading OpenNeuro MEG dataset (ds000246) with streaming...")
    try:
        row_count = _try_huggingface_stream(output_path)
        source = "huggingface:openneuro/ds000246"
    except Exception as hf_error:
        print(
            f"Hugging Face path failed ({hf_error}); trying OpenNeuro S3.",
            file=sys.stderr,
        )
        try:
            row_count = _stream_openneuro_s3(output_path)
            source = "openneuro-s3:ds000246"
        except Exception as s3_error:
            error_msg = (
                "Failed to download real MEG data from both real "
                f"sources. HF error: {hf_error} | S3 error: {s3_error}"
            )
            print(error_msg, file=sys.stderr)
            raise RuntimeError(error_msg) from s3_error

    print(f"Successfully saved real MEG data to {output_path}")
    print(f"Source: {source}")
    print(f"Total rows written: {row_count}")


if __name__ == "__main__":
    download_meg_streamed()