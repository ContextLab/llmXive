"""Download raw count matrices for the T-cell exhaustion project (T002).

For each GEO accession (GSE136103, GSE127465, GSE111075, GSE138852) this
script:

1. Queries the official NCBI GEO accession metadata endpoint
   (https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=<ACC>&targ=self&form=text)
   to discover the supplementary count-matrix file URLs at run time
   (no hard-coded URLs).
2. Downloads the supplementary count matrix (tabular ``.csv``/``.tsv``
   count matrices, optionally gzipped; ``.mtx``/``.h5`` accepted as a
   fallback) into ``data/raw/<accession>/counts/`` with retries.
3. Records SHA-256 checksums of every downloaded file in
   ``data/manifest.yaml`` (schema-valid ``Dataset`` entries, see
   ``contracts/dataset.schema.yaml``) and, for backward compatibility,
   in ``data/state.yaml``.
4. Computes ``marker_gene_fraction`` against the required marker list
   (PD-1/PDCD1, LAG3, TOX, HAVCR2, metabolic markers, exhaustion
   signature, T-cell/CD3 markers) from the REAL downloaded matrix and
   fails loudly (exit 1) if the fraction is < 0.80 (FR-010/SC-005).

The CLI accepts both the run-book invocation
(``python code/download_data.py --datasets GSE136103 GSE127465 GSE111075
GSE138852 --output data/raw/``) and the comma-separated form used in
the quickstart stage commands.

No synthetic fallback exists anywhere in this module: a failed real
fetch raises and the run fails.
"""

import argparse
import csv
import gzip
import hashlib
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GEO_METADATA_URL = (
    "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
    "?acc={acc}&targ=self&form=text"
)

DEFAULT_DATASETS = ["GSE136103", "GSE127465", "GSE111075", "GSE138852"]

# Required marker list (FR-010): PD-1, exhaustion signature, metabolic
# markers and T-cell identity markers.  Comparison is case-insensitive so
# both human (PDCD1) and mouse (Pdcd1) symbols match.
MARKER_GENES = [
    "PDCD1",   # PD-1
    "LAG3",
    "TOX",
    "HAVCR2",
    "TIGIT",
    "CTLA4",
    "ENTPD1",
    "LAYN",
    "TNFRSF9",
    "CD3D",
    "CD3E",
    "CD8A",
    "CD8B",
    "GZMB",
    "LDHA",    # metabolic markers
    "SLC2A1",
    "HK2",
    "PFKFB3",
]

MAX_RETRIES = 5
MAX_FILE_BYTES = 1_500_000_000        # skip single files larger than 1.5 GB
TOTAL_BUDGET_BYTES = 5_000_000_000    # total download budget per run
TIME_BUDGET_SECONDS = 520             # wall-clock guard for the whole run
MAX_EXTRA_FILES = 3                   # extra (non-primary) files per dataset

_SCHEMA_CANDIDATES = [
    Path("specs") / "001-single-cell-trajectories-of-t-cell-exhaustion"
    / "contracts" / "dataset.schema.yaml",
    Path("..") / "specs" / "001-single-cell-trajectories-of-t-cell-exhaustion"
    / "contracts" / "dataset.schema.yaml",
]


# ---------------------------------------------------------------------------
# Checksum / state helpers (public API, kept from the previous version)
# ---------------------------------------------------------------------------
def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 checksum of *file_path*."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def update_state(dataset_id: str, metadata: Dict[str, Any]) -> None:
    """Write *metadata* for *dataset_id* into ``data/state.yaml``."""
    project_root = Path(__file__).resolve().parent.parent
    state_path = project_root / "data" / "state.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)

    if state_path.exists():
        try:
            with state_path.open("r") as f:
                state = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            state = {}
    else:
        state = {}

    state.setdefault("datasets", {})
    state["datasets"][dataset_id] = metadata

    with state_path.open("w") as f:
        yaml.dump(state, f, default_flow_style=False)


# ---------------------------------------------------------------------------
# GEO discovery
# ---------------------------------------------------------------------------
def _geo_series_ftp_base(gse_id: str) -> str:
    """Return the base FTP URL for a GEO series."""
    if not re.match(r"^GSE\d+$", gse_id):
        raise ValueError(f"Invalid GEO series identifier: {gse_id}")
    prefix = gse_id[:-3] + "nnn"
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{prefix}/{gse_id}/suppl/"


def _list_ftp_directory(url: str) -> List[str]:
    """Return a list of filenames present in the given FTP/HTTP directory."""
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        html = r.text
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to list directory {url}: {e}") from e

    links = re.findall(r'href="([^"?]+)"', html)
    files = [
        link
        for link in links
        if not link.startswith(("http", "/", "?", "#", "mailto:", "tel:"))
        and not link.endswith("/")
    ]
    return files


def _fetch_geo_metadata(gse_id: str) -> Dict[str, Any]:
    """Query the NCBI GEO accession metadata endpoint for *gse_id*.

    Returns a dict with the series ``title`` and the list of
    ``supplementary_files`` URLs.  Retries up to MAX_RETRIES times and
    raises on total failure (no silent fallback).
    """
    url = GEO_METADATA_URL.format(acc=gse_id)
    last_exc: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            text = r.text
            suppl: List[str] = []
            title = ""
            for line in text.splitlines():
                if line.startswith("!Series_supplementary_file"):
                    u = line.split("=", 1)[1].strip()
                    if u:
                        suppl.append(u)
                elif line.startswith("!Series_title") and not title:
                    title = line.split("=", 1)[1].strip()
            if not suppl:
                raise RuntimeError(
                    f"GEO metadata for {gse_id} lists no supplementary files"
                )
            # de-duplicate, preserve order
            return {
                "title": title,
                "supplementary_files": list(dict.fromkeys(suppl)),
            }
        except Exception as e:  # noqa: BLE001 - retry any transient error
            last_exc = e
            logger.warning(
                "Metadata fetch attempt %d/%d for %s failed: %s",
                attempt, MAX_RETRIES, gse_id, e,
            )
            time.sleep(2 * attempt)
    raise RuntimeError(f"Failed to fetch GEO metadata for {gse_id}: {last_exc}")


def _remote_size(url: str) -> Optional[int]:
    """Return the remote Content-Length of *url* (None if unknown)."""
    try:
        r = requests.head(url, timeout=30, allow_redirects=True)
        if r.ok and "Content-Length" in r.headers:
            return int(r.headers["Content-Length"])
    except requests.RequestException:
        return None
    return None


_KEYWORDS = ("count", "matrix", "expr", "tpm", "rpkm", "umi", "raw")


def _candidate_score(url: str) -> int:
    """Rank a supplementary URL: lower score = better count-matrix candidate."""
    name = url.lower()
    tabular = name.endswith((".csv", ".tsv", ".csv.gz", ".tsv.gz"))
    known_ext = tabular or name.endswith(
        (".txt", ".txt.gz", ".mtx", ".mtx.gz", ".h5", ".h5ad")
    )
    keyword = any(k in name for k in _KEYWORDS)
    if not known_ext:
        return 4
    if tabular and keyword:
        return 0
    if tabular:
        return 1
    if keyword:
        return 2
    return 3


def _select_matrix_urls(urls: List[str]) -> List[str]:
    """Order supplementary URLs by count-matrix likelihood, smallest first."""
    scored: List[Tuple[int, Optional[int], int, str]] = []
    for idx, url in enumerate(urls):
        score = _candidate_score(url)
        size = _remote_size(url) if score <= 2 and len(scored) < 24 else None
        scored.append((score, size if size is not None else 10**15, idx, url))
    scored.sort()
    return [u for _, _, _, u in scored]


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
def _download_file(url: str, dest_path: Path) -> None:
    """Stream-download a file from *url* to *dest_path* with retries."""
    logger.info("Downloading %s -> %s", url, dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    last_exc: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with requests.get(url, stream=True, timeout=(30, 120)) as r:
                r.raise_for_status()
                size = int(r.headers.get("Content-Length", 0) or 0)
                if size and size > MAX_FILE_BYTES:
                    raise RuntimeError(
                        f"{url} is too large ({size} bytes > "
                        f"{MAX_FILE_BYTES} budget)"
                    )
                with dest_path.open("wb") as out_file:
                    for chunk in r.iter_content(1 << 20):
                        if chunk:
                            out_file.write(chunk)
            if dest_path.stat().st_size == 0:
                raise RuntimeError(f"Downloaded file {dest_path} is empty")
            return
        except Exception as e:  # noqa: BLE001 - retry any transient error
            last_exc = e
            logger.warning(
                "Download attempt %d/%d for %s failed: %s",
                attempt, MAX_RETRIES, url, e,
            )
            if dest_path.exists():
                dest_path.unlink()
            time.sleep(2 * attempt)
    raise RuntimeError(f"Failed to download {url}: {last_exc}")


# ---------------------------------------------------------------------------
# Matrix parsing (real data only)
# ---------------------------------------------------------------------------
def _open_text(path: Path):
    """Open *path* as text, transparently handling gzip."""
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", newline="")
    return open(path, "rt", newline="")


def _extract_genes_and_dims(path: Path) -> Tuple[List[str], int, int]:
    """Extract gene identifiers and matrix dimensions from a real matrix.

    Supports tabular count matrices (``.csv``/``.tsv``, optionally
    gzipped) in either orientation (genes x cells or cells x genes).
    Raises for non-tabular formats (the caller then tries other files).
    """
    if path.name.lower().endswith((".h5", ".h5ad", ".mtx", ".mtx.gz")):
        raise RuntimeError(
            f"Cannot extract gene symbols from {path.name} "
            "(non-tabular format); a tabular count matrix is required"
        )
    with _open_text(path) as f:
        first_line = f.readline()
        if "\t" in first_line:
            delim = "\t"
        elif "," in first_line:
            delim = ","
        else:
            raise RuntimeError(
                f"Cannot detect delimiter in {path.name} "
                "(expected tab or comma)"
            )
        f.seek(0)
        reader = csv.reader(f, delimiter=delim)
        try:
            header = next(reader)
        except StopIteration as e:
            raise RuntimeError(f"Matrix file {path.name} is empty") from e
        second = next(reader, None)

        genes_as_rows = False
        if second and len(second) > 1:
            try:
                float(second[1])
                genes_as_rows = True
            except (ValueError, TypeError):
                genes_as_rows = False

        genes: List[str] = []
        if genes_as_rows:
            # rows = genes, columns = cells
            if second and second[0]:
                genes.append(second[0])
            n_rows = 1
            for row in reader:
                if not row:
                    continue
                if row[0]:
                    genes.append(row[0])
                n_rows += 1
                if n_rows >= 200_000:
                    break
            n_genes = len(genes)
            n_cells = max(len(header) - 1, 0)
        else:
            # rows = cells, columns = genes
            genes = [g for g in header[1:] if g]
            n_genes = len(genes)
            n_cells = 1 if second else 0
            for row in reader:
                if row:
                    n_cells += 1
                    if n_cells >= 200_000:
                        break
    if n_genes == 0:
        raise RuntimeError(f"No gene identifiers found in {path.name}")
    return genes, n_cells, n_genes


def compute_marker_fraction(
    gene_names: List[str],
) -> Tuple[float, List[str], List[str]]:
    """Compute the fraction of the required marker list present (FR-010).

    Returns (fraction, found_markers, missing_markers).  Matching is
    case-insensitive so mouse symbols (e.g. ``Pdcd1``) also match.
    """
    gene_set = {str(g).strip().upper() for g in gene_names if str(g).strip()}
    found = [m for m in MARKER_GENES if m in gene_set]
    missing = [m for m in MARKER_GENES if m not in gene_set]
    return len(found) / len(MARKER_GENES), found, missing


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------
def _load_schema(project_root: Path) -> Optional[Dict[str, Any]]:
    for cand in _SCHEMA_CANDIDATES:
        p = (cand if cand.is_absolute() else project_root / cand)
        if p.exists():
            with p.open("r") as f:
                return yaml.safe_load(f)
    return None


def _validate_entry(entry: Dict[str, Any], schema: Optional[Dict[str, Any]]) -> None:
    """Validate a Dataset entry against contracts/dataset.schema.yaml."""
    if schema is None:
        logger.warning("dataset.schema.yaml not found; skipping validation")
        return
    import jsonschema

    jsonschema.validate(instance=entry, schema=schema)


def _update_manifest(project_root: Path, dataset_id: str,
                     entry: Dict[str, Any]) -> None:
    """Write a schema-valid Dataset entry into ``data/manifest.yaml``."""
    manifest_path = project_root / "data" / "manifest.yaml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    if manifest_path.exists():
        try:
            with manifest_path.open("r") as f:
                manifest = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            manifest = {}
    else:
        manifest = {}
    manifest.setdefault("datasets", {})
    manifest["datasets"][dataset_id] = entry
    with manifest_path.open("w") as f:
        yaml.dump(manifest, f, default_flow_style=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def _configure_logging(project_root: Path) -> None:
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "download.log"),
        ],
        force=True,
    )


def _process_dataset(gse: str, raw_root: Path, project_root: Path,
                     schema: Optional[Dict[str, Any]],
                     start_time: float) -> Dict[str, Any]:
    """Download and validate a single GEO dataset; return the manifest entry."""
    logger.info("Processing %s ...", gse)
    gse_dir = raw_root / gse
    counts_dir = gse_dir / "counts"
    counts_dir.mkdir(parents=True, exist_ok=True)

    # 1. Discover supplementary file URLs from the GEO metadata endpoint.
    try:
        meta = _fetch_geo_metadata(gse)
        urls = meta["supplementary_files"]
        logger.info(
            "Found %d supplementary file(s) for %s via GEO metadata endpoint",
            len(urls), gse,
        )
    except RuntimeError:
        logger.warning(
            "GEO metadata endpoint failed for %s; falling back to the "
            "NCBI FTP supplementary directory listing", gse,
        )
        base = _geo_series_ftp_base(gse)
        names = _list_ftp_directory(base)
        if not names:
            raise RuntimeError(f"No supplementary files found for {gse}")
        urls = [base + n for n in names]

    # 2. Select and download count-matrix files.
    ordered = _select_matrix_urls(urls)
    if not ordered:
        raise RuntimeError(f"No candidate supplementary files for {gse}")

    downloaded_bytes = 0
    local_files: List[Path] = []
    for i, url in enumerate(ordered):
        primary = i == 0
        if not primary:
            if len(local_files) >= MAX_EXTRA_FILES:
                break
            if time.monotonic() - start_time > TIME_BUDGET_SECONDS:
                logger.info("Time budget reached; skipping extra files for %s", gse)
                break
        filename = url.rstrip("/").split("/")[-1]
        dest = counts_dir / filename
        size = _remote_size(url)
        if dest.exists() and dest.stat().st_size > 0 and (
                size is None or dest.stat().st_size == size):
            logger.info("Reusing existing file %s", dest)
        else:
            if not primary and size and (
                    downloaded_bytes + size > TOTAL_BUDGET_BYTES):
                logger.info("Skipping %s (total budget)", filename)
                continue
            _download_file(url, dest)
        downloaded_bytes += dest.stat().st_size
        local_files.append(dest)

    if not local_files:
        raise RuntimeError(f"Failed to download any files for {gse}")

    # 3. SHA-256 checksums of every downloaded file.
    checksums = {p.name: calculate_sha256(p) for p in local_files}
    primary_file = local_files[0]

    # 4. Marker-gene fraction from the real matrix (FR-010).
    genes: Optional[List[str]] = None
    n_cells = 0
    n_genes = 0
    parse_error: Optional[Exception] = None
    for cand in local_files:
        try:
            genes, n_cells, n_genes = _extract_genes_and_dims(cand)
            primary_file = cand
            break
        except Exception as e:  # noqa: BLE001 - try next candidate file
            parse_error = e
            logger.warning("Could not parse %s: %s", cand.name, e)
    if genes is None:
        raise RuntimeError(
            f"Could not extract gene identifiers for {gse} from any "
            f"downloaded file: {parse_error}"
        )

    fraction, found, missing = compute_marker_fraction(genes)
    logger.info(
        "Marker-gene fraction for %s: %.3f (%d/%d present; missing: %s)",
        gse, fraction, len(found), len(MARKER_GENES),
        ", ".join(missing) if missing else "none",
    )
    if fraction < 0.80:
        raise RuntimeError(
            f"FR-010 violated for {gse}: marker_gene_fraction "
            f"{fraction:.3f} < 0.80. Missing markers: {', '.join(missing)}"
        )

    entry = {
        "dataset_id": gse,
        "source": "NCBI GEO accession metadata endpoint "
                  f"({GEO_METADATA_URL.format(acc=gse)})",
        "raw_counts_path": str(primary_file.relative_to(project_root)),
        "metadata_path": "",
        "checksum": checksums[primary_file.name],
        "cell_count": int(n_cells),
        "gene_count": int(n_genes),
        "marker_gene_fraction": round(fraction, 4),
        "status": "available",
    }
    _validate_entry(entry, schema)
    _update_manifest(project_root, gse, entry)
    update_state(
        gse,
        {
            "dataset_id": gse,
            "source": entry["source"],
            "raw_counts_path": entry["raw_counts_path"],
            "checksum": entry["checksum"],
            "counts_checksum": entry["checksum"],
            "all_file_checksums": checksums,
            "cell_count": entry["cell_count"],
            "gene_count": entry["gene_count"],
            "marker_gene_fraction": entry["marker_gene_fraction"],
            "missing_markers": missing,
            "status": "available",
        },
    )
    logger.info("Successfully prepared %s.", gse)
    return entry


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download raw GEO count matrices, record SHA-256 checksums in "
            "data/manifest.yaml and verify the marker-gene fraction (>= 0.80)."
        )
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=DEFAULT_DATASETS,
        help=(
            "GEO accessions, space- or comma-separated "
            "(default: GSE136103 GSE127465 GSE111075 GSE138852)."
        ),
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw",
        help="Output directory for raw data (default: data/raw).",
    )
    args = parser.parse_args()

    gse_ids = [
        part
        for token in args.datasets
        for part in token.split(",")
        if part.strip()
    ]

    project_root = Path(__file__).resolve().parent.parent
    _configure_logging(project_root)

    out_arg = Path(args.output)
    raw_root = out_arg if out_arg.is_absolute() else project_root / out_arg
    raw_root.mkdir(parents=True, exist_ok=True)

    schema = _load_schema(project_root)
    start_time = time.monotonic()

    failures: List[str] = []
    for gse in gse_ids:
        try:
            _process_dataset(gse, raw_root, project_root, schema, start_time)
        except Exception as exc:  # noqa: BLE001 - record and continue
            logger.error("Failed to process %s: %s", gse, exc)
            failures.append(gse)
            update_state(
                gse,
                {"dataset_id": gse, "status": "unavailable", "error": str(exc)},
            )

    if failures:
        logger.critical("Data preparation failed for: %s", ", ".join(failures))
        sys.exit(1)
    logger.info(
        "All %d dataset(s) downloaded, checksummed and validated "
        "(marker_gene_fraction >= 0.80).", len(gse_ids),
    )


if __name__ == "__main__":
    main()
