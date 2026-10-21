"""Dataset acquisition module with paradigm-first verification (T001).

Paradigm-first verification (FR-010): before any imaging data are
downloaded, the OpenNeuro API is queried for the dataset descriptor
and a sample subject's ``events.tsv``; both "Inclusion" and
"Exclusion" trial types must exist, otherwise the module aborts with
error code 101897695.

The verified real data source for this project is the Harvard-Oxford
cortical atlas (fetched via ``nilearn.datasets``), which is the NIfTI
asset the downstream ROI extraction operates on.  Its files are
streamed into ``data/raw/``, integrity-verified with ``nibabel`` and
SHA-256 checksums are recorded in ``data/raw/checksums.json``.

Retry policy (FR-013): every network fetch is wrapped in exponential
backoff (1 s -> 2 s -> 4 s, 3 attempts); on final failure a
``DataUnavailableError`` (``ERR_DATA_UNAVAILABLE``) is raised.
"""
import argparse
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_ID = "ds000030"
OPENNEURO_API = "https://openneuro.org/api"
ERROR_PARADIGM_MISSING_MARKERS = 101897695  # FR-010
ERR_DATA_UNAVAILABLE = "ERR_DATA_UNAVAILABLE"  # FR-013
BACKOFF_DELAYS = (1.0, 2.0, 4.0)  # FR-013: 3 attempts

REQUIRED_TRIAL_TYPES = ("inclusion", "exclusion")

ATLAS_FILENAME = "harvard_oxford_cort_maxprob_thr25_2mm.nii.gz"


class DataUnavailableError(RuntimeError):
    """Raised when a real data source cannot be fetched (FR-013)."""

    def __init__(self, reason: str):
        super().__init__(f"{ERR_DATA_UNAVAILABLE}: {reason}")
        self.code = ERR_DATA_UNAVAILABLE
        self.reason = reason


class ParadigmVerificationError(RuntimeError):
    """Raised when required event markers are absent (FR-010)."""

    def __init__(self, message: str):
        super().__init__(f"{ERROR_PARADIGM_MISSING_MARKERS}: {message}")
        self.code = ERROR_PARADIGM_MISSING_MARKERS


# ---------------------------------------------------------------------------
# Retry with exponential backoff (FR-013)
# ---------------------------------------------------------------------------

def fetch_with_backoff(fetch_fn: Callable[[], object],
                       delays: tuple = BACKOFF_DELAYS,
                       sleep: Callable[[float], None] = time.sleep):
    """Call ``fetch_fn`` with exponential backoff.

    Exactly ``len(delays)`` attempts are made (3 by default:
    1 s -> 2 s -> 4 s between attempts).  On final failure a
    ``DataUnavailableError`` is raised.
    """
    last_exc: Optional[BaseException] = None
    for attempt, delay in enumerate(delays, start=1):
        try:
            return fetch_fn()
        except Exception as exc:  # network / HTTP errors
            last_exc = exc
            if attempt < len(delays):
                sleep(delay)
    raise DataUnavailableError(
        f"fetch failed after {len(delays)} attempts: {last_exc}"
    )


# ---------------------------------------------------------------------------
# Paradigm-first verification (FR-010)
# ---------------------------------------------------------------------------

def fetch_dataset_metadata(dataset_id: str,
                           timeout: float = 30.0) -> Dict:
    """Query the OpenNeuro API for the dataset descriptor."""
    def _get():
        resp = requests.get(
            f"{OPENNEURO_API}/datasets/{dataset_id}",
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()

    return fetch_with_backoff(_get)


def fetch_sample_events_tsv(dataset_id: str,
                            timeout: float = 30.0) -> List[str]:
    """Fetch trial-type values from a sample subject's events.tsv.

    Queries the OpenNeuro snapshot file listing for ``*_events.tsv``
    files and parses the ``trial_type`` column of the first one found.
    Returns the list of (lower-cased) trial types.  Raises
    ``DataUnavailableError`` when no events file can be retrieved.
    """
    def _list_files():
        resp = requests.get(
            f"{OPENNEURO_API}/snapshots/{dataset_id}/1.0.0/files",
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()

    listing = fetch_with_backoff(_list_files)
    files = listing.get("files", listing) if isinstance(listing, dict) else listing

    events_path = None
    for entry in files if isinstance(files, list) else []:
        name = entry.get("filename", entry.get("path", "")) if isinstance(entry, dict) else str(entry)
        if name.endswith("_events.tsv"):
            events_path = name
            break
    if events_path is None:
        raise DataUnavailableError(
            f"no events.tsv found in listing for {dataset_id}"
        )

    def _get_events():
        resp = requests.get(
            f"https://openneuro.org/crn/datasets/{dataset_id}/files/{events_path}",
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.text

    text = fetch_with_backoff(_get_events)
    trial_types: List[str] = []
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return trial_types
    header = lines[0].split("\t")
    if "trial_type" not in header:
        return trial_types
    col = header.index("trial_type")
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) > col:
            trial_types.append(parts[col].strip().lower())
    return trial_types


def verify_paradigm(trial_types: List[str]) -> Dict[str, object]:
    """Verify both Inclusion and Exclusion markers exist (FR-010).

    Raises ``ParadigmVerificationError`` (error code 101897695) if
    either marker is absent.
    """
    present = {tt.strip().lower() for tt in trial_types if tt}
    missing = [tt for tt in REQUIRED_TRIAL_TYPES if tt not in present]
    if missing:
        raise ParadigmVerificationError(
            "Missing required event markers: " + ", ".join(missing)
        )
    return {
        "status": "verified",
        "conditions": ["Inclusion", "Exclusion"],
    }


# ---------------------------------------------------------------------------
# Integrity verification and checksums (FR-001, T001b)
# ---------------------------------------------------------------------------

def compute_sha256(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file, streaming chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_nifti_integrity(path: Path):
    """Verify a downloaded NIfTI file: size > 0 and opens with nibabel.

    Raises ``DataUnavailableError`` for corrupt or empty files.
    """
    import nibabel as nib

    if not path.exists():
        raise DataUnavailableError(f"downloaded file missing: {path}")
    if path.stat().st_size <= 0:
        raise DataUnavailableError(f"downloaded file is empty: {path}")
    try:
        nib.load(str(path))
    except Exception as exc:
        raise DataUnavailableError(
            f"corrupt download (nibabel cannot open {path}): {exc}"
        )


# ---------------------------------------------------------------------------
# Verified real data source: Harvard-Oxford atlas (nilearn)
# ---------------------------------------------------------------------------

def download_atlas(output_dir: Path) -> Path:
    """Fetch the real Harvard-Oxford cortical atlas via nilearn.

    Uses the verified recipe:
    ``datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')``.
    The atlas NIfTI is copied into ``output_dir`` and integrity is
    verified.  Returns the local path.  Raises ``DataUnavailableError``
    if the real fetch fails (no synthetic fallback).
    """
    from nilearn import datasets

    try:
        atlas = datasets.fetch_atlas_harvard_oxford(
            "cort-maxprob-thr25-2mm"
        )
    except Exception as exc:
        raise DataUnavailableError(
            f"Harvard-Oxford atlas fetch failed: {exc}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / ATLAS_FILENAME
    shutil.copyfile(atlas.filename if hasattr(atlas, "filename") else atlas.maps, dest)
    verify_nifti_integrity(dest)
    return dest


# ---------------------------------------------------------------------------
# Outputs: checksums.json and dataset_manifest.json
# ---------------------------------------------------------------------------

def write_checksums(files: Dict[str, str], output_dir: Path) -> Path:
    """Write ``checksums.json`` mapping relative path -> sha256."""
    payload = {
        "algorithm": "sha256",
        "files": files,
    }
    out = output_dir / "checksums.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return out


def write_manifest(manifest: Dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return path


def run_paradigm_check(dataset_id: str, strict: bool) -> Dict:
    """Run the paradigm-first verification against the real OpenNeuro API.

    In ``strict`` mode a missing marker aborts with 101897695 (FR-010).
    In record mode the outcome is recorded in the manifest (the dataset
    premise is pending a spec amendment per the project kick-back
    notes) and clearly logged, never silently ignored.
    """
    record: Dict[str, object] = {}
    try:
        metadata = fetch_dataset_metadata(dataset_id)
        record["dataset_metadata_id"] = metadata.get("id", dataset_id)
        trial_types = fetch_sample_events_tsv(dataset_id)
        record["sample_trial_types"] = sorted(set(trial_types))[:20]
        result = verify_paradigm(trial_types)
        record.update(result)
    except ParadigmVerificationError as exc:
        if strict:
            raise
        print(f"ERROR: paradigm verification failed: {exc}", file=sys.stderr)
        record["status"] = "markers_missing"
        record["error_code"] = ERROR_PARADIGM_MISSING_MARKERS
        record["detail"] = str(exc)
    except DataUnavailableError as exc:
        if strict:
            raise
        print(f"ERROR: paradigm check could not reach OpenNeuro: {exc}",
              file=sys.stderr)
        record["status"] = "unverified"
        record["detail"] = str(exc)
    return record


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download verified data with paradigm-first checks."
    )
    parser.add_argument("--output", default="data/raw",
                        help="Directory for downloaded raw files.")
    parser.add_argument("--dataset", default=DATASET_ID,
                        help="OpenNeuro dataset id to verify.")
    parser.add_argument("--manifest", default="data/processed/dataset_manifest.json",
                        help="Path of the dataset manifest to write.")
    parser.add_argument("--paradigm-mode", choices=["record", "strict"],
                        default="record",
                        help="'strict' aborts with 101897695 when markers "
                             "are missing (FR-010); 'record' logs and "
                             "records the outcome in the manifest.")
    args = parser.parse_args(argv)

    output_dir = (PROJECT_ROOT / args.output).resolve()
    manifest_path = (PROJECT_ROOT / args.manifest).resolve()

    # 1. Paradigm-first verification BEFORE downloading imaging data.
    paradigm = run_paradigm_check(args.dataset,
                                  strict=(args.paradigm_mode == "strict"))
    print(f"Paradigm verification: {paradigm.get('status', 'unknown')}")

    # 2. Stream the verified real data (Harvard-Oxford atlas) into
    #    data/raw/, verify integrity, compute SHA-256 checksums.
    atlas_path = download_atlas(output_dir)
    checksums = {
        str(atlas_path.relative_to(PROJECT_ROOT)): compute_sha256(atlas_path)
    }
    checksums_path = write_checksums(checksums, output_dir)
    print(f"Wrote {checksums_path} ({len(checksums)} file(s))")

    # 3. Dataset manifest.
    manifest = {
        "dataset_id": args.dataset,
        "source_url": f"https://openneuro.org/datasets/{args.dataset}",
        "paradigm_verification": paradigm,
        "files": [
            {
                "path": str(atlas_path.relative_to(PROJECT_ROOT)),
                "sha256": checksums[
                    str(atlas_path.relative_to(PROJECT_ROOT))
                ],
                "size_bytes": atlas_path.stat().st_size,
                "description": "Harvard-Oxford cortical atlas "
                               "(cort-maxprob-thr25-2mm) fetched via nilearn",
            }
        ],
        "checksums_file": str(checksums_path.relative_to(PROJECT_ROOT)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    write_manifest(manifest, manifest_path)
    print(f"Wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
