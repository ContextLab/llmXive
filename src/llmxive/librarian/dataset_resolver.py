"""Deterministic dataset resolver (spec: dataset-resolver design).

Finds real datasets via dataset_sources, verifies reachability (reusing
librarian.verify) + a sample-stream format sniff, ranks, and returns the top-N
verified candidates per dataset intent for injection into the Planner prompt.
"""
from __future__ import annotations

import csv as _csv
import io
import json
import zipfile
from dataclasses import dataclass, field

import requests

from llmxive.librarian.dataset_sources import DatasetCandidate, USER_AGENT

_SAMPLE_BYTES = 256 * 1024   # cap the sample download at 256 KB
_SNIFF_TIMEOUT = 20


@dataclass(frozen=True)
class FormatReport:
    parsed: bool
    format: str | None
    downloaded_bytes: int
    error: str | None = None


def _detect_and_parse(sample: bytes, url: str) -> tuple[bool, str | None]:
    # Binary container formats by magic bytes.
    if sample[:2] == b"PK":
        try:
            zipfile.ZipFile(io.BytesIO(sample))  # may raise on a truncated sample
            return True, "zip"
        except zipfile.BadZipFile:
            # A truncated-but-valid zip header still indicates a zip download.
            return True, "zip"
    if sample[:2] == b"\x1f\x8b":
        return True, "gzip"
    if sample[:8] == b"\x89HDF\r\n\x1a\n":
        return True, "hdf5"
    if sample[:4] == b"PAR1":
        return True, "parquet"
    # Text formats.
    try:
        text = sample.decode("utf-8")
    except UnicodeDecodeError:
        return False, None
    stripped = text.lstrip()
    if stripped[:1] in "{[":
        try:
            json.loads(text)
            return True, "json"
        except ValueError:
            # JSON Lines: each non-empty line parses.
            lines = [ln for ln in text.splitlines() if ln.strip()][:-1]
            if lines and all(_is_json(ln) for ln in lines):
                return True, "jsonl"
            return False, None
    if "<html" in stripped[:200].lower():
        return False, None
    # CSV/TSV: csv.Sniffer + >=2 columns on the first full row.
    try:
        dialect = _csv.Sniffer().sniff(text[:4096])
        rows = list(_csv.reader(io.StringIO(text), dialect))
        if rows and len(rows[0]) >= 2:
            return True, "tsv" if dialect.delimiter == "\t" else "csv"
    except _csv.Error:
        pass
    return False, None


def _is_json(line: str) -> bool:
    try:
        json.loads(line)
        return True
    except ValueError:
        return False


def sniff_format(url: str) -> FormatReport:
    try:
        with requests.get(url, stream=True, headers={"User-Agent": USER_AGENT}, timeout=_SNIFF_TIMEOUT) as r:
            if r.status_code >= 400:
                return FormatReport(False, None, 0, f"HTTP {r.status_code}")
            sample = r.raw.read(_SAMPLE_BYTES, decode_content=True) or b""
    except (requests.RequestException, OSError) as exc:
        return FormatReport(False, None, 0, str(exc))
    ok, fmt = _detect_and_parse(sample, url)
    return FormatReport(ok, fmt, len(sample), None if ok else "unrecognized/non-dataset content")
